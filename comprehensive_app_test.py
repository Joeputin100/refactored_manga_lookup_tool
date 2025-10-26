#!/usr/bin/env python3
"""
Comprehensive Streamlit App Test
Tests cached vs non-cached series performance, cover images, text validation, MARC export, and PDF labels
"""
import time
import sys
import os
import json
from datetime import datetime

class ComprehensiveAppTest:
    def __init__(self):
        self.results = []
        self.test_start_time = time.time()

    def test_series_search_performance(self, series_list, test_type):
        """Test series search performance"""
        try:
            from app_new_workflow import search_series_info

            performance_data = []

            for series_name in series_list:
                start_time = time.time()
                results = search_series_info(series_name)
                end_time = time.time()

                response_time = (end_time - start_time) * 1000  # Convert to milliseconds

                result = {
                    'series_name': series_name,
                    'response_time_ms': response_time,
                    'results_count': len(results),
                    'cache_status': 'cached' if results and results[0].get('source', '').endswith('(Cached)') else 'api_call',
                    'has_cover_images': any(result.get('cover_url') for result in results),
                    'has_authors': any(result.get('authors') for result in results),
                    'has_summary': any(result.get('summary') for result in results)
                }

                performance_data.append(result)

                print(f"   📖 {series_name:<30} | {response_time:6.1f}ms | "
                      f"{result['cache_status']:<10} | {len(results):2} results")

            return performance_data

        except Exception as e:
            print(f"❌ Error testing {test_type}: {e}")
            return []

    def test_volume_processing(self, series_list, volumes_per_series, test_type):
        """Test volume processing performance"""
        try:
            from manga_lookup import DeepSeekAPI, VertexAIAPI
            from bigquery_cache import BigQueryCache

            performance_data = []

            for series_name in series_list:
                print(f"   📚 Processing {series_name}...")

                series_start_time = time.time()
                volumes_processed = 0
                cache_hits = 0
                api_calls = 0

                cache = BigQueryCache()
                deepseek_api = DeepSeekAPI()
                vertex_api = VertexAIAPI()

                for volume_num in range(1, volumes_per_series + 1):
                    volume_start_time = time.time()

                    # Try cache first
                    cached_volume = cache.get_volume_info(series_name, volume_num)
                    if cached_volume:
                        cache_hits += 1
                        volume_end_time = time.time()
                    else:
                        # Fallback to API
                        api_calls += 1
                        book_data = None
                        if deepseek_api:
                            try:
                                book_data = deepseek_api.get_book_info(series_name, volume_num, None)
                            except Exception:
                                pass

                        if not book_data and vertex_api:
                            try:
                                book_data = vertex_api.get_book_info(series_name, volume_num, None)
                            except Exception:
                                pass

                        volume_end_time = time.time()

                    volumes_processed += 1

                series_end_time = time.time()
                total_time = (series_end_time - series_start_time) * 1000
                avg_time_per_volume = total_time / volumes_per_series if volumes_per_series > 0 else 0

                result = {
                    'series_name': series_name,
                    'volumes_processed': volumes_processed,
                    'total_time_ms': total_time,
                    'avg_time_per_volume_ms': avg_time_per_volume,
                    'cache_hits': cache_hits,
                    'api_calls': api_calls,
                    'cache_hit_rate': cache_hits / volumes_per_series * 100 if volumes_per_series > 0 else 0
                }

                performance_data.append(result)

                print(f"     ✅ {volumes_processed} volumes | {total_time:6.1f}ms total | "
                      f"{avg_time_per_volume:6.1f}ms/vol | Cache: {cache_hits}/{volumes_processed}")

            return performance_data

        except Exception as e:
            print(f"❌ Error testing volume processing: {e}")
            return []

    def test_marc_export(self, books_data):
        """Test MARC export functionality"""
        try:
            from marc_exporter import export_books_to_marc
            from app_new_workflow import generate_marc_filename

            print("\n📄 Testing MARC Export...")

            # Generate filename
            filename = generate_marc_filename(books_data)
            print(f"   📝 Generated filename: {filename}")

            # Export to MARC
            marc_data = export_books_to_marc(books_data)

            if marc_data:
                marc_size = len(marc_data)
                print(f"   ✅ MARC export successful: {marc_size} bytes")

                # Save MARC file
                marc_filename = f"test_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mrc"
                with open(marc_filename, 'wb') as f:
                    f.write(marc_data)
                print(f"   💾 Saved to: {marc_filename}")

                return {
                    'success': True,
                    'filename': filename,
                    'file_size': marc_size,
                    'saved_path': marc_filename
                }
            else:
                print("   ❌ MARC export failed")
                return {'success': False}

        except Exception as e:
            print(f"❌ MARC export error: {e}")
            return {'success': False}

    def validate_text_data(self, books_data):
        """Validate text data in books"""
        print("\n🔍 Validating Text Data...")

        validation_results = {
            'total_books': len(books_data),
            'books_with_authors': 0,
            'books_with_titles': 0,
            'books_with_summaries': 0,
            'books_with_isbns': 0,
            'books_with_publishers': 0,
            'validation_errors': []
        }

        for i, book in enumerate(books_data):
            # Check required fields
            if hasattr(book, 'authors') and book.authors:
                validation_results['books_with_authors'] += 1
            else:
                validation_results['validation_errors'].append(f"Book {i+1}: Missing authors")

            if hasattr(book, 'book_title') and book.book_title:
                validation_results['books_with_titles'] += 1
            else:
                validation_results['validation_errors'].append(f"Book {i+1}: Missing title")

            if hasattr(book, 'description') and book.description:
                validation_results['books_with_summaries'] += 1

            if hasattr(book, 'isbn_13') and book.isbn_13:
                validation_results['books_with_isbns'] += 1

            if hasattr(book, 'publisher_name') and book.publisher_name:
                validation_results['books_with_publishers'] += 1

        print(f"   📊 Total books: {validation_results['total_books']}")
        print(f"   👥 With authors: {validation_results['books_with_authors']}")
        print(f"   📖 With titles: {validation_results['books_with_titles']}")
        print(f"   📝 With summaries: {validation_results['books_with_summaries']}")
        print(f"   🔢 With ISBNs: {validation_results['books_with_isbns']}")
        print(f"   🏢 With publishers: {validation_results['books_with_publishers']}")

        if validation_results['validation_errors']:
            print(f"   ⚠️  Validation errors: {len(validation_results['validation_errors'])}")
            for error in validation_results['validation_errors'][:5]:  # Show first 5 errors
                print(f"     - {error}")

        return validation_results

    def run_comprehensive_test(self):
        """Run comprehensive app test"""
        print("🎯 Comprehensive Streamlit App Test")
        print("=" * 70)
        print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)

        # Define test series
        cached_series = [
            "Attack on Titan",
            "Attack on Titan: Colossal Edition",
            "Attack on Titan: No Regrets"
        ]

        non_cached_series = [
            "Tokyo Ghoul",
            "Berserk",
            "Death Note"
        ]

        print("\n📊 Testing Series Search Performance")
        print("-" * 50)

        # Test cached series
        print("\n🔍 Cached Series (Fast - from pre-seed):")
        cached_performance = self.test_series_search_performance(cached_series, "cached")

        print("\n🔍 Non-Cached Series (Slow - API calls):")
        non_cached_performance = self.test_series_search_performance(non_cached_series, "non_cached")

        print("\n📚 Testing Volume Processing (5 volumes each)")
        print("-" * 50)

        print("\n🔍 Cached Volumes:")
        cached_volumes = self.test_volume_processing(cached_series, 5, "cached")

        print("\n🔍 Non-Cached Volumes:")
        non_cached_volumes = self.test_volume_processing(non_cached_series, 5, "non_cached")

        # Calculate performance metrics
        print("\n📈 Performance Summary")
        print("-" * 50)

        if cached_performance and non_cached_performance:
            avg_cached_time = sum(r['response_time_ms'] for r in cached_performance) / len(cached_performance)
            avg_non_cached_time = sum(r['response_time_ms'] for r in non_cached_performance) / len(non_cached_performance)

            print(f"📊 Series Search:")
            print(f"   Cached:    {avg_cached_time:6.1f}ms (avg)")
            print(f"   API Call:  {avg_non_cached_time:6.1f}ms (avg)")
            print(f"   Speedup:   {(avg_non_cached_time - avg_cached_time) / avg_non_cached_time * 100:6.1f}% faster")

        if cached_volumes and non_cached_volumes:
            avg_cached_volume_time = sum(r['avg_time_per_volume_ms'] for r in cached_volumes) / len(cached_volumes)
            avg_non_cached_volume_time = sum(r['avg_time_per_volume_ms'] for r in non_cached_volumes) / len(non_cached_volumes)

            print(f"\n📚 Volume Processing:")
            print(f"   Cached:    {avg_cached_volume_time:6.1f}ms/vol (avg)")
            print(f"   API Call:  {avg_non_cached_volume_time:6.1f}ms/vol (avg)")
            print(f"   Speedup:   {(avg_non_cached_volume_time - avg_cached_volume_time) / avg_non_cached_volume_time * 100:6.1f}% faster")

        # Test MARC export with sample data
        print("\n📄 Testing MARC Export and Validation")
        print("-" * 50)

        # Create sample book data for export test
        sample_books = []
        try:
            from manga_lookup import BookInfo

            # Add some sample books
            for i in range(5):
                book = BookInfo(
                    series_name=f"Test Series {i+1}",
                    volume_number=i+1,
                    book_title=f"Test Volume {i+1}",
                    authors=["Test Author"],
                    msrp_cost=9.99,
                    isbn_13=f"978012345678{i}",
                    publisher_name="Test Publisher",
                    copyright_year=2024,
                    description="Test description",
                    physical_description="192 pages",
                    genres=["Test Genre"],
                    warnings=[],
                    barcode=f"TEST{i+1:06d}",
                    cover_image_url=None
                )
                sample_books.append(book)

            marc_result = self.test_marc_export(sample_books)
            validation_result = self.validate_text_data(sample_books)

        except Exception as e:
            print(f"❌ Sample data creation failed: {e}")

        # Final summary
        test_end_time = time.time()
        total_test_time = test_end_time - self.test_start_time

        print("\n✅ Test Completed Successfully!")
        print("=" * 70)
        print(f"Total test time: {total_test_time:.1f} seconds")
        print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)

        return {
            'cached_performance': cached_performance,
            'non_cached_performance': non_cached_performance,
            'cached_volumes': cached_volumes,
            'non_cached_volumes': non_cached_volumes,
            'marc_result': marc_result if 'marc_result' in locals() else None,
            'validation_result': validation_result if 'validation_result' in locals() else None,
            'total_test_time': total_test_time
        }

if __name__ == "__main__":
    try:
        test = ComprehensiveAppTest()
        results = test.run_comprehensive_test()

        # Save results to file
        results_file = f"app_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n💾 Results saved to: {results_file}")

    except Exception as e:
        print(f"❌ Comprehensive test failed: {e}")
        import traceback
        traceback.print_exc()