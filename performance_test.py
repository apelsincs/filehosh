#!/usr/bin/env python3
"""
Скрипт для тестирования производительности файлового хостинга 0123.ru

Этот скрипт тестирует:
- Одновременные загрузки файлов
- Скорость обработки запросов
- Пропускную способность
- Стабильность под нагрузкой
"""

import asyncio
import aiohttp
import time
import random
import string
import os
from concurrent.futures import ThreadPoolExecutor
import statistics
import json
from typing import List, Dict, Any

class PerformanceTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = []
        self.session = None
        
    async def create_session(self):
        """Создает aiohttp сессию"""
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)
        
    async def close_session(self):
        """Закрывает aiohttp сессию"""
        if self.session:
            await self.session.close()
            
    def generate_test_file(self, size_kb: int = 10) -> bytes:
        """Генерирует тестовый файл указанного размера"""
        return b'0' * (size_kb * 1024)
        
    def generate_random_code(self, length: int = 6) -> str:
        """Генерирует случайный код файла"""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
        
    async def upload_file(self, file_size_kb: int = 10) -> Dict[str, Any]:
        """Загружает один файл и возвращает результат"""
        start_time = time.time()
        
        try:
            # Генерируем тестовый файл
            file_data = self.generate_test_file(file_size_kb)
            filename = f"test_{file_size_kb}kb_{int(time.time())}.txt"
            
            # Создаем FormData
            data = aiohttp.FormData()
            data.add_field('file', file_data, filename=filename)
            data.add_field('custom_code', self.generate_random_code())
            
            # Отправляем запрос
            async with self.session.post(f"{self.base_url}/", data=data, ssl=False) as response:
                response_time = time.time() - start_time
                response_data = await response.json()
                
                return {
                    'success': response.status == 200,
                    'status_code': response.status,
                    'response_time': response_time,
                    'file_size_kb': file_size_kb,
                    'response_data': response_data
                }
                
        except Exception as e:
            response_time = time.time() - start_time
            return {
                'success': False,
                'error': str(e),
                'response_time': response_time,
                'file_size_kb': file_size_kb
            }
            
    async def download_file(self, file_url: str) -> Dict[str, Any]:
        """Скачивает файл и возвращает результат"""
        start_time = time.time()
        
        try:
            async with self.session.get(file_url, ssl=False) as response:
                response_time = time.time() - start_time
                content_length = len(await response.read())
                
                return {
                    'success': response.status == 200,
                    'status_code': response.status,
                    'response_time': response_time,
                    'content_length': content_length
                }
                
        except Exception as e:
            response_time = time.time() - start_time
            return {
                'success': False,
                'error': str(e),
                'response_time': response_time
            }
            
    async def test_concurrent_uploads(self, num_uploads: int = 10, file_size_kb: int = 10) -> List[Dict[str, Any]]:
        """Тестирует одновременные загрузки файлов"""
        print(f"Тестируем {num_uploads} одновременных загрузок файлов по {file_size_kb}KB...")
        
        tasks = [self.upload_file(file_size_kb) for _ in range(num_uploads)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Обрабатываем исключения
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append({
                    'success': False,
                    'error': str(result),
                    'response_time': 0
                })
            else:
                processed_results.append(result)
                
        return processed_results
        
    async def test_upload_throughput(self, duration_seconds: int = 60, target_rps: int = 10) -> List[Dict[str, Any]]:
        """Тестирует пропускную способность загрузок в течение указанного времени"""
        print(f"Тестируем пропускную способность {target_rps} запросов/сек в течение {duration_seconds} секунд...")
        
        results = []
        start_time = time.time()
        request_interval = 1.0 / target_rps
        
        while time.time() - start_time < duration_seconds:
            request_start = time.time()
            
            # Загружаем файл
            result = await self.upload_file(10)  # 10KB файлы
            results.append(result)
            
            # Ждем до следующего запроса
            elapsed = time.time() - request_start
            if elapsed < request_interval:
                await asyncio.sleep(request_interval - elapsed)
                
        return results
        
    async def test_mixed_load(self, num_requests: int = 100) -> List[Dict[str, Any]]:
        """Тестирует смешанную нагрузку (загрузки + скачивания)"""
        print(f"Тестируем смешанную нагрузку: {num_requests} запросов...")
        
        results = []
        
        # Сначала загружаем несколько файлов
        upload_results = await self.test_concurrent_uploads(5, 10)
        results.extend(upload_results)
        
        # Получаем URL загруженных файлов
        file_urls = []
        for result in upload_results:
            if result.get('success') and result.get('response_data', {}).get('url'):
                file_urls.append(result['response_data']['url'])
                
        # Теперь тестируем скачивания
        if file_urls:
            download_tasks = []
            for _ in range(num_requests - 5):
                url = random.choice(file_urls)
                download_tasks.append(self.download_file(url))
                
            download_results = await asyncio.gather(*download_tasks, return_exceptions=True)
            
            # Обрабатываем результаты скачиваний
            for result in download_results:
                if isinstance(result, Exception):
                    results.append({
                        'success': False,
                        'error': str(result),
                        'response_time': 0,
                        'type': 'download'
                    })
                else:
                    result['type'] = 'download'
                    results.append(result)
                    
        return results
        
    def analyze_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Анализирует результаты тестирования"""
        if not results:
            return {}
            
        successful_requests = [r for r in results if r.get('success')]
        failed_requests = [r for r in results if not r.get('success')]
        
        response_times = [r.get('response_time', 0) for r in results if r.get('response_time')]
        
        analysis = {
            'total_requests': len(results),
            'successful_requests': len(successful_requests),
            'failed_requests': len(failed_requests),
            'success_rate': len(successful_requests) / len(results) * 100 if results else 0,
            'avg_response_time': statistics.mean(response_times) if response_times else 0,
            'min_response_time': min(response_times) if response_times else 0,
            'max_response_time': max(response_times) if response_times else 0,
            'median_response_time': statistics.median(response_times) if response_times else 0,
            'requests_per_second': len(results) / max(response_times) if response_times else 0,
            'errors': [r.get('error') for r in failed_requests if r.get('error')]
        }
        
        return analysis
        
    def print_results(self, test_name: str, results: List[Dict[str, Any]]):
        """Выводит результаты тестирования"""
        analysis = self.analyze_results(results)
        
        print(f"\n{'='*60}")
        print(f"РЕЗУЛЬТАТЫ ТЕСТА: {test_name}")
        print(f"{'='*60}")
        
        if analysis:
            print(f"Всего запросов: {analysis['total_requests']}")
            print(f"Успешных: {analysis['successful_requests']}")
            print(f"Неудачных: {analysis['failed_requests']}")
            print(f"Процент успеха: {analysis['success_rate']:.2f}%")
            print(f"Среднее время ответа: {analysis['avg_response_time']:.3f}с")
            print(f"Минимальное время: {analysis['min_response_time']:.3f}с")
            print(f"Максимальное время: {analysis['max_response_time']:.3f}с")
            print(f"Медианное время: {analysis['median_response_time']:.3f}с")
            print(f"Запросов в секунду: {analysis['requests_per_second']:.2f}")
            
            if analysis['errors']:
                print(f"\nОшибки:")
                for error in set(analysis['errors']):
                    count = analysis['errors'].count(error)
                    print(f"  - {error}: {count} раз")
        else:
            print("Нет результатов для анализа")
            
    async def run_all_tests(self):
        """Запускает все тесты производительности"""
        print("🚀 ЗАПУСК ТЕСТИРОВАНИЯ ПРОИЗВОДИТЕЛЬНОСТИ 0123.ru")
        print(f"Тестируем сервер: {self.base_url}")
        
        await self.create_session()
        
        try:
            # Тест 1: Одновременные загрузки
            print("\n1️⃣ ТЕСТ ОДНОВРЕМЕННЫХ ЗАГРУЗОК")
            concurrent_results = await self.test_concurrent_uploads(20, 10)
            self.print_results("Одновременные загрузки (20 файлов по 10KB)", concurrent_results)
            
            # Тест 2: Пропускная способность
            print("\n2️⃣ ТЕСТ ПРОПУСКНОЙ СПОСОБНОСТИ")
            throughput_results = await self.test_upload_throughput(30, 5)  # 30 сек, 5 запросов/сек
            self.print_results("Пропускная способность (5 запросов/сек, 30 сек)", throughput_results)
            
            # Тест 3: Смешанная нагрузка
            print("\n3️⃣ ТЕСТ СМЕШАННОЙ НАГРУЗКИ")
            mixed_results = await self.test_mixed_load(50)
            self.print_results("Смешанная нагрузка (50 запросов)", mixed_results)
            
            # Тест 4: Большие файлы
            print("\n4️⃣ ТЕСТ БОЛЬШИХ ФАЙЛОВ")
            large_file_results = await self.test_concurrent_uploads(5, 1000)  # 5 файлов по 1MB
            self.print_results("Большие файлы (5 файлов по 1MB)", large_file_results)
            
            # Общий анализ
            all_results = concurrent_results + throughput_results + mixed_results + large_file_results
            print("\n📊 ОБЩИЙ АНАЛИЗ")
            self.print_results("Все тесты", all_results)
            
            # Сохраняем результаты в файл
            timestamp = int(time.time())
            filename = f"performance_test_results_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': timestamp,
                    'base_url': self.base_url,
                    'tests': {
                        'concurrent_uploads': self.analyze_results(concurrent_results),
                        'throughput': self.analyze_results(throughput_results),
                        'mixed_load': self.analyze_results(mixed_results),
                        'large_files': self.analyze_results(large_file_results),
                        'overall': self.analyze_results(all_results)
                    },
                    'raw_results': all_results
                }, f, indent=2, ensure_ascii=False)
                
            print(f"\n💾 Результаты сохранены в файл: {filename}")
            
        finally:
            await self.close_session()
            
    def generate_report(self, results_file: str):
        """Генерирует отчет на основе результатов тестирования"""
        try:
            with open(results_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            print("\n📋 ОТЧЕТ О ПРОИЗВОДИТЕЛЬНОСТИ")
            print("="*60)
            
            overall = data['tests']['overall']
            
            print(f"🎯 ОБЩИЕ ПОКАЗАТЕЛИ:")
            print(f"   • Всего запросов: {overall['total_requests']}")
            print(f"   • Процент успеха: {overall['success_rate']:.1f}%")
            print(f"   • Среднее время ответа: {overall['avg_response_time']:.3f}с")
            print(f"   • Запросов в секунду: {overall['requests_per_second']:.1f}")
            
            print(f"\n📈 РЕКОМЕНДАЦИИ:")
            
            if overall['success_rate'] < 95:
                print("   ⚠️  Низкий процент успеха - проверить настройки сервера")
                
            if overall['avg_response_time'] > 2:
                print("   ⚠️  Медленные ответы - оптимизировать обработку запросов")
                
            if overall['requests_per_second'] < 10:
                print("   ⚠️  Низкая пропускная способность - увеличить ресурсы сервера")
                
            if overall['success_rate'] >= 95 and overall['avg_response_time'] < 1:
                print("   ✅ Отличная производительность!")
                
            print(f"\n🔧 ОПТИМИЗАЦИЯ:")
            print(f"   • Использовать CDN для статических файлов")
            print(f"   • Настроить кеширование (Redis)")
            print(f"   • Оптимизировать базу данных")
            print(f"   • Использовать Gunicorn с несколькими воркерами")
            print(f"   • Настроить Nginx как прокси-сервер")
            
        except FileNotFoundError:
            print(f"Файл {results_file} не найден")
        except json.JSONDecodeError:
            print(f"Ошибка чтения файла {results_file}")

async def main():
    """Главная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Тестирование производительности 0123.ru')
    parser.add_argument('--url', default='http://localhost:8000', 
                       help='URL сервера для тестирования')
    parser.add_argument('--report', help='Файл с результатами для генерации отчета')
    
    args = parser.parse_args()
    
    if args.report:
        # Генерируем отчет
        tester = PerformanceTester()
        tester.generate_report(args.report)
    else:
        # Запускаем тестирование
        tester = PerformanceTester(args.url)
        await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
