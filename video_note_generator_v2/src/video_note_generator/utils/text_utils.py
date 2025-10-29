"""
文本处理工具模块
"""
import re
from typing import List


def split_content(
    text: str,
    max_chars: int = 2000,
    overlap_chars: int = 200
) -> List[str]:
    """
    按段落分割文本，保持上下文连贯性

    Args:
        text: 要分割的文本
        max_chars: 每个分块的最大字符数
        overlap_chars: 分块之间重叠的字符数

    Returns:
        分割后的文本列表
    """
    if not text or not text.strip():
        return []

    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = []
    current_length = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        para_length = len(para)

        # 如果单个段落超过最大长度，按句子分割
        if para_length > max_chars:
            if current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = []
                current_length = 0

            # 按句子分割
            sentences = re.split(r'([。！？])', para)
            current_sentence = []
            current_sentence_length = 0

            for i in range(0, len(sentences), 2):
                sentence = sentences[i]
                if i + 1 < len(sentences):
                    sentence += sentences[i + 1]

                if current_sentence_length + len(sentence) > max_chars and current_sentence:
                    chunks.append(''.join(current_sentence))
                    # 保留最后一个句子作为重叠
                    if overlap_chars > 0 and len(current_sentence) > 0:
                        current_sentence = [current_sentence[-1], sentence]
                        current_sentence_length = len(current_sentence[-2]) + len(sentence)
                    else:
                        current_sentence = [sentence]
                        current_sentence_length = len(sentence)
                else:
                    current_sentence.append(sentence)
                    current_sentence_length += len(sentence)

            if current_sentence:
                chunks.append(''.join(current_sentence))

        else:
            # 如果加上这个段落会超过最大长度，保存当前块
            if current_length + para_length > max_chars and current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                # 保留最后一段作为重叠
                if overlap_chars > 0 and current_chunk:
                    overlap_text = current_chunk[-1]
                    if len(overlap_text) > overlap_chars:
                        overlap_text = overlap_text[-overlap_chars:]
                    current_chunk = [overlap_text, para]
                    current_length = len(overlap_text) + para_length
                else:
                    current_chunk = [para]
                    current_length = para_length
            else:
                current_chunk.append(para)
                current_length += para_length

    # 保存最后一个块
    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))

    return chunks


def extract_urls(text: str) -> List[str]:
    """
    从文本中提取所有URL

    Args:
        text: 输入文本

    Returns:
        提取到的URL列表
    """
    url_patterns = [
        # 标准URL
        r'https?://[^\s<>\[\]"\']+[^\s<>\[\]"\'.,]',
        # Bilibili BV号
        r'BV[a-zA-Z0-9]{10}',
        # 抖音短链接
        r'v\.douyin\.com/[a-zA-Z0-9]+',
    ]

    urls = []
    for pattern in url_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            url = match.group()
            # 为BV号添加完整的bilibili前缀
            if url.startswith('BV'):
                url = f'https://www.bilibili.com/video/{url}'
            # 为抖音短链接添加https
            elif url.startswith('v.douyin.com'):
                url = f'https://{url}'
            urls.append(url)

    # 去重并保持顺序
    seen = set()
    return [url for url in urls if not (url in seen or seen.add(url))]


def clean_text(text: str) -> str:
    """
    清理文本，移除多余的空白字符

    Args:
        text: 输入文本

    Returns:
        清理后的文本
    """
    # 移除多余的空白字符
    text = re.sub(r'\s+', ' ', text)
    # 移除首尾空白
    text = text.strip()
    # 恢复段落分隔
    text = re.sub(r' ?(\n) ?', r'\1', text)
    return text


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    截断文本到指定长度

    Args:
        text: 输入文本
        max_length: 最大长度
        suffix: 截断后添加的后缀

    Returns:
        截断后的文本
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix
