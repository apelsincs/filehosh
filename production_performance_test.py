#!/usr/bin/env python3
"""
Простой тест производительности для production сервера 0123.ru
Запускайте на VPS после развертывания для проверки производительности
"""

import requests
import time
import statistics
import json
from datetime import datetime
import os

class ProductionPerformanceTest:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.results = []
        self.session = requests.Session()
        
    def test_homepage(self, iterations: int = 10):
        """Тестирует главную страницу"""
        print(f"🏠 Тестирование главной страницы ({iterations} запросов)...")
        
        times = []
        for i in range(iterations):
            start_time = time.time()
            try:
                response = self.session.get(f"{self.base_url}/", timeout=10)
                response_time = (time.time() - start_time) * 1000  # в миллисекундах
                times.append(response_time)
                
                if response.status_code == 200:
                    print(f"  ✅ Запрос {i+1}: {response_time:.1f}ms")
                else:
                    print(f"  ❌ Запрос {i+1}: HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"  ❌ Запрос {i+1}: Ошибка - {e}")
                
        if times:
            avg_time = statistics.mean(times)
            min_time = min(times)
            max_time = max(times)
            print(f"  📊 Результаты: среднее={avg_time:.1f}ms, мин={min_time:.1f}ms, макс={max_time:.1f}ms")
            
        return times
    
    def test_file_upload(self, file_size_kb: int = 100, iterations: int = 5):
        """Тестирует загрузку файлов"""
        print(f"📤 Тестирование загрузки файлов {file_size_kb}KB ({iterations} запросов)...")
        
        # Создаем тестовый файл
        test_file_content = b'0' * (file_size_kb * 1024)
        
        times = []
        for i in range(iterations):
            start_time = time.time()
            try:
                files = {'file': (f'test_{i}.txt', test_file_content, 'text/plain')}
                data = {'custom_code': f'TEST{i:03d}'}
                
                response = self.session.post(f"{self.base_url}/", files=files, data=data, timeout=30)
                response_time = (time.time() - start_time) * 1000
                times.append(response_time)
                
                if response.status_code == 200:
                    print(f"  ✅ Загрузка {i+1}: {response_time:.1f}ms")
                else:
                    print(f"  ❌ Загрузка {i+1}: HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"  ❌ Загрузка {i+1}: Ошибка - {e}")
                
        if times:
            avg_time = statistics.mean(times)
            min_time = min(times)
            max_time = max(times)
            print(f"  📊 Результаты: среднее={avg_time:.1f}ms, мин={min_time:.1f}ms, макс={max_time:.1f}ms")
            
        return times
    
    def test_file_download(self, file_url: str, iterations: int = 5):
        """Тестирует скачивание файла"""
        print(f"📥 Тестирование скачивания файла ({iterations} запросов)...")
        
        times = []
        for i in range(iterations):
            start_time = time.time()
            try:
                response = self.session.get(file_url, timeout=30)
                response_time = (time.time() - start_time) * 1000
                times.append(response_time)
                
                if response.status_code == 200:
                    print(f"  ✅ Скачивание {i+1}: {response_time:.1f}ms")
                else:
                    print(f"  ❌ Скачивание {i+1}: HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"  ❌ Скачивание {i+1}: Ошибка - {e}")
                
        if times:
            avg_time = statistics.mean(times)
            min_time = min(times)
            max_time = max(times)
            print(f"  📊 Результаты: среднее={avg_time:.1f}ms, мин={min_time:.1f}ms, макс={max_time:.1f}ms")
            
        return times
    
    def test_concurrent_requests(self, concurrent: int = 10, iterations: int = 5):
        """Тестирует одновременные запросы"""
        print(f"🔄 Тестирование одновременных запросов ({concurrent} одновременных, {iterations} итераций)...")
        
        import threading
        
        def make_request():
            start_time = time.time()
            try:
                response = self.session.get(f"{self.base_url}/", timeout=10)
                response_time = (time.time() - start_time) * 1000
                return response_time, response.status_code
            except Exception as e:
                return None, str(e)
        
        all_times = []
        for i in range(iterations):
            print(f"  🚀 Итерация {i+1}/{iterations}...")
            
            threads = []
            results = []
            
            # Создаем потоки
            for j in range(concurrent):
                thread = threading.Thread(target=lambda: results.append(make_request()))
                threads.append(thread)
            
            # Запускаем все потоки
            start_time = time.time()
            for thread in threads:
                thread.start()
            
            # Ждем завершения
            for thread in threads:
                thread.join()
            
            total_time = (time.time() - start_time) * 1000
            
            # Анализируем результаты
            successful_times = [r[0] for r in results if r[0] is not None]
            if successful_times:
                avg_time = statistics.mean(successful_times)
                all_times.append(avg_time)
                print(f"    📊 Среднее время: {avg_time:.1f}ms, общее время: {total_time:.1f}ms")
            else:
                print(f"    ❌ Все запросы завершились с ошибкой")
        
        if all_times:
            overall_avg = statistics.mean(all_times)
            print(f"  📊 Общий результат: среднее время {overall_avg:.1f}ms")
            
        return all_times
    
    def run_full_test(self):
        """Запускает полный тест производительности"""
        print("🚀 Запуск полного теста производительности 0123.ru")
        print(f"🌐 Тестируемый сервер: {self.base_url}")
        print(f"⏰ Время начала: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Тест главной страницы
        homepage_times = self.test_homepage(20)
        print()
        
        # Тест загрузки файлов
        upload_times = self.test_file_upload(100, 10)
        print()
        
        # Тест одновременных запросов
        concurrent_times = self.test_concurrent_requests(20, 3)
        print()
        
        # Сводка результатов
        print("=" * 60)
        print("📊 СВОДКА РЕЗУЛЬТАТОВ:")
        print("=" * 60)
        
        if homepage_times:
            avg_homepage = statistics.mean(homepage_times)
            print(f"🏠 Главная страница: {avg_homepage:.1f}ms (среднее)")
            
        if upload_times:
            avg_upload = statistics.mean(upload_times)
            print(f"📤 Загрузка файлов: {avg_upload:.1f}ms (среднее)")
            
        if concurrent_times:
            avg_concurrent = statistics.mean(concurrent_times)
            print(f"🔄 Одновременные запросы: {avg_concurrent:.1f}ms (среднее)")
        
        # Оценка производительности
        print("\n🎯 ОЦЕНКА ПРОИЗВОДИТЕЛЬНОСТИ:")
        if homepage_times and upload_times:
            avg_response = (statistics.mean(homepage_times) + statistics.mean(upload_times)) / 2
            
            if avg_response < 200:
                print("  🟢 ОТЛИЧНО! Сервер работает очень быстро")
            elif avg_response < 500:
                print("  🟡 ХОРОШО! Сервер работает с приемлемой скоростью")
            elif avg_response < 1000:
                print("  🟠 УДОВЛЕТВОРИТЕЛЬНО! Сервер работает медленно")
            else:
                print("  🔴 ПЛОХО! Сервер работает очень медленно")
        
        print(f"\n⏰ Время завершения: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("🎉 Тест завершен!")

def main():
    """Главная функция"""
    import sys
    
    if len(sys.argv) != 2:
        print("Использование: python production_performance_test.py <URL_СЕРВЕРА>")
        print("Пример: python production_performance_test.py http://YOUR_SERVER_IP")
        sys.exit(1)
    
    base_url = sys.argv[1].rstrip('/')
    
    # Проверяем доступность сервера
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        if response.status_code == 200:
            print(f"✅ Сервер {base_url} доступен")
        else:
            print(f"⚠️ Сервер {base_url} отвечает с кодом {response.status_code}")
    except Exception as e:
        print(f"❌ Не удается подключиться к серверу {base_url}: {e}")
        sys.exit(1)
    
    # Запускаем тест
    tester = ProductionPerformanceTest(base_url)
    tester.run_full_test()

if __name__ == "__main__":
    main()
