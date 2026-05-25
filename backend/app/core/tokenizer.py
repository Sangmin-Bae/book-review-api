import re
from nltk.stem import PorterStemmer
from pecab import PeCab

# 앱 시작 시 한 번만 초기화 - 모듈 레벨 싱글톤 패턴
# PeCab은 내부 사전 로딩에 시간이 걸리기 때문
# 매 함수 호출마다 초기화하면 성능이 크게 저하됨
_pecab = PeCab()
_stemmer = PorterStemmer()

# 검색 토큰으로 유지할 한국어 품사 태그
# NNG: 일반 명사 (파친코, 소설)
# NNP: 고유 명사 (이민진, 서울)
# NNB: 의존 명사 (것, 수)
# VV: 동사 어간 (읽, 가)
# VA: 형용사 어간 (좋, 크)
_KO_VALID_POS = {"NNG", "NNP", "NNB", "VV", "VA"}


def _tokenize_korean(text: str) -> list[str]:
    """
    한국어 형태소 분석

    PeCab으로 형태소를 분리하고 의미있는 품사만 추출
    조사(을/를/이/가), 어미(었/겠/다) 등 검색에 불필요한 형태소는 제거
    """
    # pos(): 각 형태소와 품사 태그를 튜플로 반환
    # 예: [('파친코', 'NNG'), ('를', 'JKO'), ('읽', 'VV'), ('었', 'EP'), ('다', 'EF')]
    morphs = _pecab.pos(text)

    return [
        token for token, pos in morphs
        if pos in _KO_VALID_POS  # 유효한 품사만 유지
        and len(token) > 1  # 1글자 형태소 제거 (노이즈 가능성 높음)
    ]


def _tokenize_english(text: str) -> list[str]:
    """
    영어 어간 추출(Stemming)

    소문자로 변환 후 PorterStemmer로 어간 추출
    예: "running" -> "run", "novels" -> "novel"
    """
    # 영어 단어만 추출 (한글, 숫자, 특수문자 제외)
    words = re.findall(r'[a-zA-Z]+', text)

    return [
        _stemmer.stem(token.lower())  # 소문자 변환 + 어간 추출
        for token in words
        if len(token) > 1  # 1글자 영어 단어 제거 (a, I 등)
    ]


def tokenize(text: str) -> str:
    """
    한국어 + 영어 혼합 텍스트 토크나이징

    한국어 형태소 분석과 영어 어간 추출을 결합해서
    search_tokens 컬럼에 저장할 토큰 문자열을 생성

    반환값: 공백으로 구분된 토큰 문자열
    예: "파친코를 읽은 Pachinko novels" -> "파친코 읽 pachinko novel"
    """
    if not text:
        return ""

    ko_tokens = _tokenize_korean(text)
    en_tokens = _tokenize_english(text)

    # 한국어 + 영어 토큰을 합쳐서 공백으로 구분된 문자열로 반환
    # trigram 검색 시 이 문자열을 대상으로 검색
    all_tokens = ko_tokens + en_tokens
    return " ".join(all_tokens)