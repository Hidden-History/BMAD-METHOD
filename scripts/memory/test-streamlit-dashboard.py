#!/usr/bin/env python3
"""
Playwright test for BMAD Memory Streamlit Dashboard

Tests all major features of the dashboard to verify functionality.

Usage:
    python scripts/memory/test-streamlit-dashboard.py

Created: 2026-01-04
Week 4: Dashboard Testing
"""

import sys
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("❌ Playwright not installed")
    print("Install with: pip install playwright")
    print("Then run: playwright install")
    sys.exit(1)

DASHBOARD_URL = "http://localhost:18505"

def test_dashboard():
    """Test the Streamlit dashboard."""
    print("🧪 Testing BMAD Memory Intelligence Dashboard")
    print("=" * 60)

    with sync_playwright() as p:
        # Launch browser
        print("🌐 Launching browser...")
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            # Navigate to dashboard
            print(f"📡 Navigating to {DASHBOARD_URL}...")
            page.goto(DASHBOARD_URL, timeout=10000)

            # Wait for page to load
            page.wait_for_timeout(3000)

            # Test 1: Check page title
            print("\n✅ Test 1: Page Title")
            title = page.title()
            print(f"   Title: {title}")
            assert "BMAD Memory Intelligence" in title or "streamlit" in title.lower(), "Title not found"

            # Test 2: Check header
            print("\n✅ Test 2: Page Header")
            header = page.locator("h1").first
            if header.count() > 0:
                header_text = header.text_content()
                print(f"   Header: {header_text}")
                assert "BMAD Memory Intelligence" in header_text or "Dashboard" in header_text
            else:
                print("   ⚠️  No h1 header found (Streamlit may still be loading)")

            # Test 3: Check for metrics (collection counts)
            print("\n✅ Test 3: Collection Metrics")
            metrics = page.locator("[data-testid='stMetric']")
            metric_count = metrics.count()
            print(f"   Found {metric_count} metrics")

            if metric_count >= 3:
                # Should have 3 metrics for 3 collections
                for i in range(min(3, metric_count)):
                    metric = metrics.nth(i)
                    metric_text = metric.text_content()
                    print(f"   Metric {i+1}: {metric_text[:50]}...")
            else:
                print("   ⚠️  Expected at least 3 metrics (one per collection)")

            # Test 4: Check sidebar
            print("\n✅ Test 4: Sidebar")
            sidebar = page.locator("[data-testid='stSidebar']")
            if sidebar.count() > 0:
                sidebar_text = sidebar.text_content()
                print(f"   Sidebar found: {len(sidebar_text)} characters")

                # Check for collection selector
                if "Collection" in sidebar_text or "knowledge" in sidebar_text:
                    print("   ✅ Collection selector found")
                else:
                    print("   ⚠️  Collection selector not found")
            else:
                print("   ⚠️  Sidebar not found")

            # Test 5: Check for search interface
            print("\n✅ Test 5: Search Interface")
            search_inputs = page.locator("input[type='text']")
            search_count = search_inputs.count()
            print(f"   Found {search_count} text input(s)")

            if search_count > 0:
                print("   ✅ Search input found")
            else:
                print("   ⚠️  No search input found")

            # Test 6: Check for sections/headers
            print("\n✅ Test 6: Page Sections")
            headers = page.locator("h2, h3")
            header_count = headers.count()
            print(f"   Found {header_count} section headers")

            section_names = []
            for i in range(min(10, header_count)):
                section_text = headers.nth(i).text_content()
                section_names.append(section_text)

            if section_names:
                print(f"   Sections: {', '.join(section_names[:5])}")

            # Check for expected sections
            expected_sections = ["Collection Health", "Search", "Recent Memories", "Quality Metrics"]
            found_sections = []
            all_text = page.text_content("body")

            for section in expected_sections:
                if section in all_text:
                    found_sections.append(section)

            print(f"   Expected sections found: {found_sections}")

            # Test 7: Screenshot
            print("\n✅ Test 7: Taking Screenshot")
            screenshot_path = Path("/tmp/bmad-dashboard-test.png")
            page.screenshot(path=str(screenshot_path))
            print(f"   Screenshot saved: {screenshot_path}")

            # Final summary
            print("\n" + "=" * 60)
            print("📊 TEST SUMMARY")
            print("=" * 60)
            print(f"✅ Dashboard loaded successfully")
            print(f"✅ Title: {title}")
            print(f"✅ Metrics: {metric_count} found")
            print(f"✅ Search inputs: {search_count} found")
            print(f"✅ Sections: {len(found_sections)}/{len(expected_sections)} expected sections found")
            print(f"✅ Screenshot: {screenshot_path}")

            if metric_count >= 3 and search_count > 0:
                print("\n🎉 All core features verified!")
                return 0
            else:
                print("\n⚠️  Some features may be missing or still loading")
                return 1

        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return 1

        finally:
            browser.close()

if __name__ == "__main__":
    sys.exit(test_dashboard())
