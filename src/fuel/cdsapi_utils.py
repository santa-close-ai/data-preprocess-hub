import logging
import cdsapi

def _set_logger() -> logging.Logger:
    # 1. Logger 객체 생성
    # 이름을 지정하지 않으면 root 로거를 얻거나, 지정된 이름의 로거를 얻습니다.
    # 일반적으로 모듈 이름을 로거 이름으로 사용하는 것이 좋습니다.
    logger = logging.getLogger("cdsapi_utils") # 현재 모듈의 이름을 로거 이름으로 사용

    # 2. 로깅 레벨 설정 (Logger 객체에 설정)
    logger.setLevel(logging.DEBUG)

    # 3. Handler 생성 (로그 메시지를 어디로 보낼지 결정)
    # 콘솔(스트림)로 보내는 핸들러
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG) # 콘솔에는 INFO 레벨만 출력

    # 4. Formatter 생성 (로그 메시지 형식 지정)
    # formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

    # 5. Handler에 Formatter 설정
    stream_handler.setFormatter(formatter)

    # 6. Logger에 Handler 추가
    logger.addHandler(stream_handler)
    return logger

logger = _set_logger()
dataset = "derived-fire-fuel-biomass"
months = list(range(12, 0, -1))

class Category:
    # 클래스 속성 (Class Attributes)
    # 모든 Months 인스턴스가 공유하며, 인스턴스 없이도 접근 가능
    DFMC = "dead_fuel_moisture_content_group"
    LFMC = "live_fuel_moisture_content_group"
    FUEL = "fuel_group"

def cdsapi_request(year: int, month: int, variable: str) -> str | None:
    year_list = [str(year)]
    month_list = ['{:02d}'.format(month)]
    request = {
        "variable": [variable],
        "version": ["1"],
        "year": year_list,
        "month": month_list,
        "area": [39, 124, 33, 132]
    }

    client = cdsapi.Client()
    result = client.retrieve(dataset, request).download()
    return result
