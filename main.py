import os
import re
import json
import requests
from fastmcp import FastMCP

mcp = FastMCP("KCSC Standards MCP")


def _fetch_kcsc_data(doc_type: str, code_number: str):
    """KCSC Open API에서 기준 원본 데이터를 가져옵니다."""
    api_key = os.environ.get("KCSC_API_KEY")

    if not api_key:
        raise RuntimeError("KCSC_API_KEY 환경변수가 설정되지 않았습니다.")

    url = f"https://kcsc.re.kr/OpenApi/CodeViewer/{doc_type}/{code_number}"
    params = {"key": api_key}

    response = requests.get(
        url,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


def _find_items(data):
    """KCSC 응답에서 기준 항목 목록을 찾습니다."""
    if isinstance(data, dict):

        if isinstance(data.get("list"), list):
            return data["list"]

        for value in data.values():
            result = _find_items(value)

            if result is not None:
                return result

    elif isinstance(data, list):

        if any(
            isinstance(item, dict)
            and (
                "contents" in item
                or "label" in item
                or "sort" in item
            )
            for item in data
        ):
            return data

        for item in data:
            result = _find_items(item)

            if result is not None:
                return result

    return None


def _is_section_title(item):
    """
    4.1.2, 4.1.3처럼 새로운 상위 조항이 시작되는지 확인합니다.
    """

    if not isinstance(item, dict):
        return False

    label = str(item.get("label", "")).strip()
    contents = str(item.get("contents", ""))

    # label 자체가 번호형 조항인 경우
    if re.match(
        r"^\d+(?:\.\d+){2,4}\s*",
        label
    ):
        return True

    # HTML 태그 제거 후 contents 확인
    plain_start = re.sub(
        r"<[^>]+>",
        "",
        contents
    ).strip()

    return bool(
        re.match(
            r"^\d+(?:\.\d+){2,4}\s+",
            plain_start
        )
    )


@mcp.tool()
def get_kcsc_standard(
    doc_type: str,
    code_number: str
) -> str:
    """
    국가건설기준센터(KCSC)의 KDS 또는 KCS 기준 전문을 조회합니다.

    doc_type:
        KDS 또는 KCS

    code_number:
        예: 142010, 142052
    """

    try:

        data = _fetch_kcsc_data(
            doc_type,
            code_number
        )

        # 기존 동작과 동일하게 원본 데이터를 반환
        return str(data)

    except requests.RequestException as e:

        return f"KCSC API 호출 오류: {e}"

    except ValueError as e:

        return f"KCSC API 응답 JSON 파싱 오류: {e}"

    except Exception as e:

        return f"오류 발생: {e}"


@mcp.tool()
def get_kcsc_section(
    doc_type: str,
    code_number: str,
    section_label: str
) -> str:
    """
    KCSC 기준 원본 데이터에서 지정한 조항을 반환합니다.

    예:

        doc_type = "KDS"
        code_number = "142052"
        section_label = "4.1.2"

    반환되는 contents는 KCSC API 원본 HTML을 그대로 유지합니다.

    <img src="data:image/gif;base64,...">
    형태의 수식 이미지도 삭제하거나 해석하지 않습니다.
    """

    try:

        data = _fetch_kcsc_data(
            doc_type,
            code_number
        )

        items = _find_items(data)

        if not items:

            return json.dumps(
                {
                    "error":
                        "KCSC 응답에서 기준 항목 목록을 찾지 못했습니다."
                },
                ensure_ascii=False
            )

        target = section_label.strip()

        start_index = None

        # 해당 조항의 시작 위치 검색
        for i, item in enumerate(items):

            label = str(
                item.get("label", "")
            ).strip()

            contents = str(
                item.get("contents", "")
            )

            plain_contents = re.sub(
                r"<[^>]+>",
                "",
                contents
            ).strip()

            if (
                label == target
                or plain_contents.startswith(target + " ")
                or re.search(
                    rf"(?<!\d){re.escape(target)}\s",
                    plain_contents
                )
            ):

                start_index = i
                break

        if start_index is None:

            return json.dumps(
                {
                    "error":
                        f"조항 '{target}'을 찾지 못했습니다."
                },
                ensure_ascii=False
            )

        # 해당 조항부터 다음 상위 조항 직전까지 추출
        selected = [
            items[start_index]
        ]

        for item in items[start_index + 1:]:

            if _is_section_title(item):
                break

            selected.append(item)

        result = {
            "doc_type": doc_type,
            "code_number": code_number,
            "section_label": target,
            "source": "KCSC Open API",
            "items": selected
        }

        # 중요:
        # contents의 HTML과 base64 이미지 데이터를
        # 수정하지 않고 그대로 반환
        return json.dumps(
            result,
            ensure_ascii=False
        )

    except requests.RequestException as e:

        return f"KCSC API 호출 오류: {e}"

    except ValueError as e:

        return f"KCSC API 응답 JSON 파싱 오류: {e}"

    except Exception as e:

        return f"오류 발생: {e}"


if __name__ == "__main__":

    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=8000
    )
