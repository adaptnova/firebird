import logging


def parse_html_extract_data_summarize(**kwargs) -> Dict[str, Any]:
    """Frequent sequence with 100% success rate

    This tool combines the following operations:
    parse_html → extract_data → summarize

    Args:
        query: Search/query parameter (if applicable)
        file_path: File path (if applicable)
        **kwargs: Additional parameters passed to underlying tools

    Returns:
        Combined result from the tool sequence
    """
    logging.info(f'Executing 3 tools in sequence')

    result = None

    # Step 1: parse_html
    try:
        step_0_result = self._execute_parse_html(**kwargs)
        result = step_0_result
    except Exception as e:
        logging.error('Error in parse_html: {}'.format(e))
        raise

    # Step 2: extract_data
    try:
        step_1_result = self._execute_extract_data(**kwargs)
        result = step_1_result
    except Exception as e:
        logging.error('Error in extract_data: {}'.format(e))
        raise

    # Step 3: summarize
    try:
        step_2_result = self._execute_summarize(**kwargs)
        result = step_2_result
    except Exception as e:
        logging.error('Error in summarize: {}'.format(e))
        raise

    return result
