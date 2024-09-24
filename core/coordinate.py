import math


class CoordinateConverter:
    def __init__(self):
        # 지도반경, 격자간격, 표준위도, 기준점, X/Y 좌표, 시작 여부 초기화
        self.Re = 6371.00877  # 지구반경 (km)
        self.grid = 5.0  # 격자간격 (km)
        self.slat1 = 30.0  # 표준위도 1
        self.slat2 = 60.0  # 표준위도 2
        self.olon = 126.0  # 기준점 경도
        self.olat = 38.0  # 기준점 위도
        self.xo = 210 / self.grid  # 기준점 X좌표
        self.yo = 675 / self.grid  # 기준점 Y좌표
        self.first = False  # 시작 여부

        # 필요한 상수들 계산
        self.PI = math.pi
        self.DEGRAD = self.PI / 180.0
        self.RADDEG = 180.0 / self.PI

        if not self.first:
            self._initialize_params()

    def _initialize_params(self):
        # 내부 변수 초기화
        re = self.Re / self.grid
        slat1 = self.slat1 * self.DEGRAD
        slat2 = self.slat2 * self.DEGRAD
        olon = self.olon * self.DEGRAD
        olat = self.olat * self.DEGRAD

        sn = math.tan(self.PI * 0.25 + slat2 * 0.5) / math.tan(self.PI * 0.25 + slat1 * 0.5)
        sn = math.log(math.cos(slat1) / math.cos(slat2)) / math.log(sn)
        sf = math.tan(self.PI * 0.25 + slat1 * 0.5)
        sf = (sf ** sn) * math.cos(slat1) / sn
        ro = math.tan(self.PI * 0.25 + olat * 0.5)
        ro = re * sf / (ro ** sn)

        # 클래스 변수로 저장
        self.re = re
        self.slat1 = slat1
        self.slat2 = slat2
        self.olon = olon
        self.olat = olat
        self.sn = sn
        self.sf = sf
        self.ro = ro
        self.first = True

    def convert(self, lon, lat, x, y, code):
        # 위경도 -> (X, Y) 변환
        if code == 0:
            return self._latlon_to_grid(lon, lat)
        # (X, Y) -> 위경도 변환
        elif code == 1:
            return self._grid_to_latlon(x, y)

    def _latlon_to_grid(self, lon, lat):
        lon = lon * self.DEGRAD
        lat = lat * self.DEGRAD

        ra = math.tan(self.PI * 0.25 + lat * 0.5)
        ra = self.re * self.sf / (ra ** self.sn)

        theta = lon - self.olon
        if theta > self.PI:
            theta -= 2.0 * self.PI
        if theta < -self.PI:
            theta += 2.0 * self.PI
        theta *= self.sn

        x = ra * math.sin(theta) + self.xo
        y = self.ro - ra * math.cos(theta) + self.yo
        return int(x + 1.5), int(y + 1.5)

    def _grid_to_latlon(self, x, y):
        xn = x - self.xo
        yn = self.ro - (y - self.yo)
        ra = math.sqrt(xn * xn + yn * yn)
        if self.sn < 0:
            ra = -ra
        alat = (self.re * self.sf / ra) ** (1.0 / self.sn)
        alat = 2.0 * math.atan(alat) - self.PI * 0.5

        if abs(xn) <= 0.0:
            theta = 0.0
        else:
            if abs(yn) <= 0.0:
                theta = self.PI * 0.5
                if xn < 0.0:
                    theta = -theta
            else:
                theta = math.atan2(xn, yn)

        alon = theta / self.sn + self.olon
        lon = alon * self.RADDEG
        lat = alat * self.RADDEG
        return lon, lat