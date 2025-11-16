#!/usr/bin/env python3
"""
Node3 Agent Download Analytics
Fetches download statistics from GitHub Releases API
"""

import requests
import json
from datetime import datetime
from typing import Dict, List

class DownloadAnalytics:
    def __init__(self, repo_owner: str, repo_name: str):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.base_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
    
    def get_all_releases(self) -> List[Dict]:
        """Fetch all releases from GitHub API"""
        url = f"{self.base_url}/releases"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    
    def get_release_stats(self, tag_name: str = None) -> Dict:
        """Get download stats for a specific release or latest"""
        if tag_name:
            url = f"{self.base_url}/releases/tags/{tag_name}"
        else:
            url = f"{self.base_url}/releases/latest"
        
        response = requests.get(url)
        response.raise_for_status()
        release = response.json()
        
        stats = {
            'tag_name': release['tag_name'],
            'name': release['name'],
            'published_at': release['published_at'],
            'total_downloads': 0,
            'assets': []
        }
        
        for asset in release['assets']:
            asset_info = {
                'name': asset['name'],
                'size': asset['size'],
                'download_count': asset['download_count'],
                'created_at': asset['created_at'],
                'browser_download_url': asset['browser_download_url']
            }
            stats['assets'].append(asset_info)
            stats['total_downloads'] += asset['download_count']
        
        return stats
    
    def get_total_downloads(self) -> Dict:
        """Get total downloads across all releases"""
        releases = self.get_all_releases()
        
        total_stats = {
            'total_downloads': 0,
            'total_releases': len(releases),
            'platforms': {
                'windows': 0,
                'linux': 0,
                'macos': 0,
                'other': 0
            },
            'releases': []
        }
        
        for release in releases:
            release_downloads = 0
            for asset in release['assets']:
                count = asset['download_count']
                release_downloads += count
                
                # Categorize by platform
                name = asset['name'].lower()
                if '.exe' in name or 'windows' in name:
                    total_stats['platforms']['windows'] += count
                elif 'linux' in name or '.tar.gz' in name:
                    total_stats['platforms']['linux'] += count
                elif '.dmg' in name or 'macos' in name or 'darwin' in name:
                    total_stats['platforms']['macos'] += count
                else:
                    total_stats['platforms']['other'] += count
            
            total_stats['releases'].append({
                'tag_name': release['tag_name'],
                'published_at': release['published_at'],
                'downloads': release_downloads
            })
            
            total_stats['total_downloads'] += release_downloads
        
        return total_stats
    
    def print_stats(self):
        """Print formatted statistics"""
        print("=" * 60)
        print("📊 NODE3 AGENT DOWNLOAD STATISTICS")
        print("=" * 60)
        print()
        
        # Total stats
        total = self.get_total_downloads()
        print(f"🌍 Total Downloads: {total['total_downloads']:,}")
        print(f"📦 Total Releases: {total['total_releases']}")
        print()
        
        # Platform breakdown
        print("🖥️  DOWNLOADS BY PLATFORM")
        print("-" * 60)
        platforms = total['platforms']
        for platform, count in platforms.items():
            if count > 0:
                percentage = (count / total['total_downloads'] * 100) if total['total_downloads'] > 0 else 0
                print(f"  {platform.capitalize():12} {count:6,} downloads ({percentage:5.1f}%)")
        print()
        
        # Latest release
        print("🚀 LATEST RELEASE")
        print("-" * 60)
        latest = self.get_release_stats()
        print(f"  Version: {latest['tag_name']}")
        print(f"  Published: {latest['published_at']}")
        print(f"  Total Downloads: {latest['total_downloads']:,}")
        print()
        print("  Assets:")
        for asset in latest['assets']:
            size_mb = asset['size'] / 1024 / 1024
            print(f"    • {asset['name']}")
            print(f"      {asset['download_count']:,} downloads ({size_mb:.1f} MB)")
        print()
        
        # Release history
        if len(total['releases']) > 1:
            print("📈 RELEASE HISTORY")
            print("-" * 60)
            for release in total['releases'][:5]:  # Show last 5 releases
                published = datetime.fromisoformat(release['published_at'].replace('Z', '+00:00'))
                print(f"  {release['tag_name']:12} {release['downloads']:6,} downloads  ({published.strftime('%Y-%m-%d')})")
        
        print()
        print("=" * 60)
    
    def export_json(self, filename: str = 'download_stats.json'):
        """Export stats to JSON file"""
        stats = self.get_total_downloads()
        with open(filename, 'w') as f:
            json.dump(stats, f, indent=2)
        print(f"✅ Stats exported to {filename}")
    
    def export_csv(self, filename: str = 'download_stats.csv'):
        """Export stats to CSV file"""
        import csv
        
        total = self.get_total_downloads()
        
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Release', 'Published Date', 'Downloads'])
            
            for release in total['releases']:
                writer.writerow([
                    release['tag_name'],
                    release['published_at'],
                    release['downloads']
                ])
        
        print(f"✅ Stats exported to {filename}")


def main():
    # Initialize analytics for your repo
    analytics = DownloadAnalytics('squirtgunhero', 'node3')
    
    # Print stats to console
    analytics.print_stats()
    
    # Export to files
    analytics.export_json('download_stats.json')
    analytics.export_csv('download_stats.csv')


if __name__ == '__main__':
    main()

