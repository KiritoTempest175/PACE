"""Non-model token counting: optional native extension, explicit Python fallback."""
import re
import logging
from core.config import get_settings
logger=logging.getLogger(__name__)

def split_for_display(text:str)->tuple[list[str],str]:
    if get_settings().tokenizer_backend=='rust':
        try:
            from pace_rust_tokenizer import tokenize_text  # optional module, not shipped in original repo
            return tokenize_text(text),'rust'
        except ImportError:
            logger.warning('Rust tokenizer unavailable; using Python approximate splitting')
    # This splitter is NOT a replacement for a model's exact HF tokenizer.
    return re.findall(r'\w+|[^\w\s]',text,flags=re.UNICODE),'python-approximate'
