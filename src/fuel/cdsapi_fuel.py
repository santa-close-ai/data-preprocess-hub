import time
from cdsapi_utils import *

def main():
    for year in range(2011, 2010, -1):
        for month in months:
            while True:
                time.sleep(10)
                result = None
                try:
                    result = cdsapi_request(year, month, Category.FUEL)
                    # print(result)
                    logger.info('Downloaded {}'.format(result))
                    break
                except Exception as e:
                    if result is not None:
                        logger.warning('Downloaded {}'.format(result))
                    else:
                        logger.warning('Download failed')
                    # 모든 예외의 에러 메시지를 출력할 때는 Exception을 사용
                    print('예외가 발생했습니다.', e)

if __name__ == "__main__":
    main()

# import cdsapi

# dataset = "derived-fire-fuel-biomass"
# request = {
#     "variable": ["fuel_group"],
#     "version": ["1"],
#     "year": ["2012"],
#     "month": ["01", "02", "03"],
#     "area": [39, 124, 33, 132]
# }

# client = cdsapi.Client()
# client.retrieve(dataset, request).download()
