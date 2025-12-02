from enum import Enum, auto
from functools import lru_cache
from re import sub
from typing import List, Optional, Tuple  # 导入类型注解，指定函数参数和返回值类型
from unicodedata import east_asian_width  # 导入获取字符宽度的函数，用于判断字符是全角还是半角


class CharType(Enum):
    """字符类型枚举类，用于区分不同类型的字符以辅助文本分词和换行"""
    SPACE = auto()  # 空格字符类型
    ASIAN = auto()  # 亚洲字符类型（如中文、日文等）
    LATIN = auto()  # 拉丁字符类型（如英文、数字等）


class TextWrap:
    """文本自动换行处理类，支持根据字符宽度（中文2，英文1）进行智能换行"""

    EAST_ASAIN_WIDTH_TABLE = {
        "F": 2,  # 全角字符宽度为2
        "H": 1,  # 半角字符宽度为1
        "W": 2,  # 宽字符宽度为2
        "A": 1,  # 半角字母宽度为1
        "N": 1,  # 半角数字宽度为1
        "Na": 1,  # 半角无宽字符宽度为1
    }

    @classmethod
    @lru_cache(maxsize=128) 
    def get_width(cls, char: str) -> int:
        """获取字符的宽度（中文2，英文1），默认返回1（处理异常字符）
        
        Args:
            char: 待获取宽度的字符
            
        Returns:
            字符的宽度（单位：字符数）
        """

        return cls.EAST_ASAIN_WIDTH_TABLE.get(east_asian_width(char), 1)

    @classmethod
    @lru_cache(maxsize=32)
    def get_text_width(cls, text: str) -> int:
        """计算文本的总宽度（按字符宽度累加）
        
        Args:
            text: 待计算宽度的文本字符串
            
        Returns:
            文本的总宽度（单位：字符数）
        """
        return sum(cls.get_width(char) for char in text)

    @classmethod
    @lru_cache(maxsize=128)
    def get_char_type(cls, char: str) -> CharType: # 判断单个字符的类型（空格/亚洲字符/拉丁字符）
        
        if char.isspace():
            return CharType.SPACE
        if cls.get_width(char) == 1:
            return CharType.LATIN
        return CharType.ASIAN 

    @classmethod
    def process_text_whitespace(cls, text: str) -> str:

        """处理文本中的空白字符：合并连续空格为单个空格，并去除首尾空格 """

        return sub(pattern=r"\s+", repl=" ", string=text).strip()

    @classmethod
    @lru_cache(maxsize=32)  # 缓存最多32个长 token 的分割结果
    def split_long_token(cls, token: str, width: int) -> List[str]:
        """将超长 token 按指定宽度分割为多个子串（按字符数分割，假设每个字符宽度为1）
        
        Args:
            token: 超长文本片段（如长英文单词）
            width: 最大分割宽度（字符数）
            
        Returns:
            分割后的子串列表
        """
        return [token[i : i + width] for i in range(0, len(token), width)]

    @classmethod
    def tokenizer(cls, text: str):
        """文本分词器：根据字符类型（SPACE/ASIAN/LATIN）将文本分割为连续同类型 token
        
        Args:
            text: 待分词的文本
            
        Yields:
            按字符类型分割的 token 字符串（如"你好abc " → ["你好", "abc", " "]）
        """
        buffer = ""
        last_char_type: Optional[CharType] = None 

        for char in text:  # 遍历文本中的每个字符
            char_type = cls.get_char_type(char)  # 获取当前字符类型

            if buffer and (char_type != last_char_type or char_type != CharType.LATIN):
                yield buffer 
                buffer = "" 

            buffer += char
            last_char_type = char_type

        yield buffer

    @classmethod
    def wrap(cls, text: str, width: int, once: bool = True) -> Tuple[str, bool]:
        """根据指定宽度对文本进行自动换行处理
        
        Args:
            text: 待换行的原始文本
            width: 单行最大显示宽度（中文算2，英文算1）
            once: 是否仅换行一次（True：只处理第一行超长部分；False：处理所有行）
            
        Returns:
            Tuple[str, bool]: 
                - wrap_text: 换行处理后的文本
                - is_wrapped: 是否发生了换行（True表示有换行，False表示未换行）
        """
        width = int(width)
        lines = text.splitlines() 
        is_wrapped = False 
        wrapped_lines = [] 

        for line in lines:
            line = cls.process_text_whitespace(line)  

            if cls.get_text_width(line) > width: 

                wrapped_line, is_wrapped = cls._wrap_line(line, width, once)
                wrapped_lines.append(wrapped_line) 

                if once:
                    wrapped_lines.append(text[len(wrapped_line) :].rstrip())
                    return "".join(wrapped_lines), is_wrapped 
            else:
                wrapped_lines.append(line)

        return "\n".join(wrapped_lines), is_wrapped

    @classmethod
    def _wrap_line(cls, text: str, width: int, once: bool = True) -> Tuple[str, bool]:
        """内部方法：处理单行文本的换行逻辑（核心换行算法）
        
        Args:
            text: 单行待换行文本
            width: 单行最大显示宽度
            once: 是否仅换行一次
            
        Returns:
            Tuple[str, bool]: 
                - 换行处理后的单行文本（可能包含换行符）
                - True（固定返回，表示当前行已处理换行）
        """
        line_buffer = "" 
        wrapped_lines = [] 
        current_width = 0 

        for token in cls.tokenizer(text): 
            token_width = cls.get_text_width(token)

            if token == " " and current_width == 0:
                continue


            if current_width + token_width <= width:
                line_buffer += token 
                current_width += token_width 

                if current_width == width:
                    wrapped_lines.append(line_buffer.rstrip()) 
                    line_buffer = ""  
                    current_width = 0 
            else:
        
                if current_width != 0:
                    wrapped_lines.append(line_buffer.rstrip())
                    line_buffer = "" 
                    current_width = 0 

    
                chunks = cls.split_long_token(token, width) 


                for chunk in chunks[:-1]:
                    wrapped_lines.append(chunk.rstrip())

        
                line_buffer = chunks[-1]
                current_width = cls.get_text_width(chunks[-1]) 

     
        if current_width != 0:
            wrapped_lines.append(line_buffer.rstrip())

        if once: 
            return "\n".join([wrapped_lines[0], " ".join(wrapped_lines[1:])]), True
        
        return "\n".join(wrapped_lines), True
