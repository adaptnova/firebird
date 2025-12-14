import logging
from typing import Dict, Any, List


def search_web_parse_html_extract_data(query: str, **kwargs) -> Dict[str, Any]:
    """Frequent sequence with 100% success rate

    This tool combines the following operations:
    search_web → parse_html → extract_data

    Args:
        query: Search/query parameter (if applicable)
        file_path: File path (if applicable)
        **kwargs: Additional parameters passed to underlying tools

    Returns:
        Combined result from the tool sequence
    """
    logging.info(f'Executing 3 tools in sequence')

    result = None

    # Step 1: search_web
    try:
        step_0_result = self._execute_search_web(**kwargs)
        result = step_0_result
    except Exception as e:
        logging.error('Error in search_web: {}'.format(e))
        raise

    # Step 2: parse_html
    try:
        step_1_result = self._execute_parse_html(**kwargs)
        result = step_1_result
    except Exception as e:
        logging.error('Error in parse_html: {}'.format(e))
        raise

    # Step 3: extract_data
    try:
        step_2_result = self._execute_extract_data(**kwargs)
        result = step_2_result
    except Exception as e:
        logging.error('Error in extract_data: {}'.format(e))
        raise

    return result
