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
    code_number: 문서 번호 (예: 142010 등)
    """
    # 환경변수에 등록된 KCSC 인증키를 불러옵니다.
    api_key = os.environ.get("KCSC_API_KEY")
    url = "https://kcsc.re.kr/OpenApi/CodeViewer.JSON"
    
    params = {
        "Type": doc_type,
        "Code": code_number,
        "Key": api_key
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return str(response.json())
        else:
            return f"API 호출 실패: 상태 코드 {response.status_code}"
    except Exception as e:
        return f"오류 발생: {e}"

if __name__ == "__main__":
    # HTTP 전송 방식으로 MCP 서버 실행
    mcp.run(transport="http", host="0.0.0.0", port=8000)