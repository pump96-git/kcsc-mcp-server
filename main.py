import os
import requests
from fastmcp import FastMCP

# MCP 서버 인스턴스 생성
mcp = FastMCP("KCSC Standards MCP")


@mcp.tool()
def get_kcsc_standard(doc_type: str, code_number: str) -> str:
    """
    국가건설기준센터(KCSC)의 KDS 또는 KCS 기준 전문을 조회합니다.

    doc_type: 문서 타입 (예: KDS 또는 KCS)
    code_number: 문서 번호 (예: 142010, 142052 등)
    """

    # 환경변수에 등록된 KCSC 인증키
    api_key = os.environ.get("KCSC_API_KEY")

    if not api_key:
        return "오류: KCSC_API_KEY 환경변수가 설정되지 않았습니다."

    # 현재 KCSC Open API 주소
    url = f"https://kcsc.re.kr/OpenApi/CodeViewer/{doc_type}/{code_number}"

    params = {
        "key": api_key
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        return str(data)

    except requests.RequestException as e:
        return f"KCSC API 호출 오류: {e}"

    except ValueError as e:
        return f"KCSC API 응답 JSON 파싱 오류: {e}"


if __name__ == "__main__":
    # HTTP 전송 방식으로 MCP 서버 실행
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=8000
    )
