#!/usr/bin/env python3
"""
Enhanced volume range display logic for the manga lookup application
"""

def format_volume_range(volumes):
    """
    Format a list of volume numbers into a human-readable range string.

    Args:
        volumes: List of volume numbers

    Returns:
        Formatted range string like "1-10" or "1,3,5,7" or "1-5,8,10"
    """
    if not volumes:
        return ""

    volumes = sorted(set(volumes))  # Remove duplicates and sort

    if len(volumes) == 1:
        return str(volumes[0])

    # Check if volumes form a continuous range
    if volumes == list(range(volumes[0], volumes[-1] + 1)):
        return f"{volumes[0]}-{volumes[-1]}"

    # Handle mixed ranges and individual volumes
    ranges = []
    current_range = [volumes[0]]

    for i in range(1, len(volumes)):
        if volumes[i] == volumes[i-1] + 1:
            current_range.append(volumes[i])
        else:
            if len(current_range) >= 3:
                ranges.append(f"{current_range[0]}-{current_range[-1]}")
            else:
                ranges.extend(str(v) for v in current_range)
            current_range = [volumes[i]]

    # Add the last range
    if len(current_range) >= 3:
        ranges.append(f"{current_range[0]}-{current_range[-1]}")
    else:
        ranges.extend(str(v) for v in current_range)

    return ",".join(ranges)


def get_series_volume_info_from_cache(series_name):
    """
    Get comprehensive volume information for a series from BigQuery cache.

    Args:
        series_name: Name of the series

    Returns:
        Dictionary with volume information
    """
    try:
        from bigquery_cache import BigQueryCache
        cache = BigQueryCache()

        # Get series info
        series_info = cache.get_series_info(series_name)

        # Get all volumes for this series
        volumes = cache.get_volumes(series_name)

        return {
            'series_info': series_info,
            'volumes': volumes,
            'total_volumes': len(volumes),
            'volume_numbers': [v.get('volume_number') for v in volumes if v.get('volume_number')],
            'cached_volumes': [v for v in volumes if v.get('cached', False)]
        }
    except Exception as e:
        print(f"❌ Error getting volume info from cache: {e}")
        return None


def display_enhanced_volume_info(series_name, processed_volumes):
    """
    Display enhanced volume information with cache data.

    Args:
        series_name: Name of the series
        processed_volumes: List of volume numbers that were processed
    """
    import streamlit as st

    # Get cache information
    cache_info = get_series_volume_info_from_cache(series_name)

    if cache_info:
        st.markdown(f"### 📚 {series_name}")

        # Series metadata columns
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if cache_info['series_info'] and cache_info['series_info'].get('authors'):
                authors = cache_info['series_info']['authors']
                if isinstance(authors, str):
                    st.write(f"**Author:** {authors}")
                elif isinstance(authors, list):
                    st.write(f"**Author:** {', '.join(authors)}")
            else:
                st.write("**Author:** Unknown")

        with col2:
            # Show processed volume range
            processed_range = format_volume_range(processed_volumes)
            st.write(f"**Processed Volumes:** {processed_range}")

        with col3:
            # Show total volumes in cache
            total_cached = cache_info['total_volumes']
            st.write(f"**Cached Volumes:** {total_cached}")

        with col4:
            # Show series status
            if cache_info['series_info'] and cache_info['series_info'].get('status'):
                status = cache_info['series_info']['status']
                status_emoji = "🟢" if status.lower() == "ongoing" else "🔵" if status.lower() == "completed" else "⚪"
                st.write(f"**Status:** {status_emoji} {status}")
            else:
                st.write("**Status:** Unknown")

        # Additional cache information
        if cache_info['series_info']:
            col5, col6 = st.columns(2)

            with col5:
                if cache_info['series_info'].get('publisher'):
                    st.write(f"**Publisher:** {cache_info['series_info']['publisher']}")

            with col6:
                if cache_info['series_info'].get('genres'):
                    genres = cache_info['series_info']['genres']
                    if isinstance(genres, str):
                        st.write(f"**Genres:** {genres}")
                    elif isinstance(genres, list):
                        st.write(f"**Genres:** {', '.join(genres)}")

        # Volume coverage information
        if cache_info['volume_numbers'] and processed_volumes:
            cached_volumes = set(cache_info['volume_numbers'])
            processed_set = set(processed_volumes)

            # Calculate coverage
            coverage = len(cached_volumes.intersection(processed_set)) / len(processed_set) * 100

            st.progress(coverage / 100)
            st.caption(f"Cache coverage: {coverage:.1f}% ({len(cached_volumes.intersection(processed_set))}/{len(processed_set)} volumes)")

    return cache_info


def create_volume_range_summary(series_entries):
    """
    Create a summary of volume ranges across all series.

    Args:
        series_entries: List of series entries from session state

    Returns:
        Summary dictionary
    """
    summary = {
        'total_series': len(series_entries),
        'total_volumes': 0,
        'volume_ranges': [],
        'series_info': []
    }

    for entry in series_entries:
        if entry.get('confirmed') and entry.get('volumes'):
            volumes = entry['volumes']
            volume_range = format_volume_range(volumes)

            summary['total_volumes'] += len(volumes)
            summary['volume_ranges'].append({
                'series_name': entry.get('selected_series', 'Unknown'),
                'volume_range': volume_range,
                'volume_count': len(volumes),
                'barcode_range': f"{entry['barcodes'][0]} - {entry['barcodes'][-1]}" if entry.get('barcodes') else "Unknown"
            })

            # Get cache info for this series
            cache_info = get_series_volume_info_from_cache(entry.get('selected_series', ''))
            summary['series_info'].append({
                'series_name': entry.get('selected_series', 'Unknown'),
                'cache_info': cache_info
            })

    return summary