import json
import random
from datetime import datetime, timedelta
import re

class IDCardGenerator:
    def __init__(self, area_data):
        """
        初始化身份证生成器
        
        Args:
            area_data: 行政区划JSON数据
        """
        self.area_data = area_data
        self.area_dict = {}
        self.provinces = []
        self.cities = {}
        self.counties = {}
        self.towns = {}  # 第四级街道地址
        
        # 民族列表（按人口比例设置权重）
        self.nations = [
            '汉', '壮', '回', '满', '维吾尔', '苗', '彝', '土家', '藏', '蒙古',
            '侗', '布依', '瑶', '白', '朝鲜', '哈尼', '黎', '哈萨克', '傣', '畲',
            '傈僳', '东乡', '仡佬', '拉祜', '佤', '水', '纳西', '羌', '土', '仫佬',
            '锡伯', '柯尔克孜', '景颇', '达斡尔', '撒拉', '布朗', '毛南', '塔吉克',
            '普米', '阿昌', '怒', '鄂温克', '京', '基诺', '德昂', '保安', '俄罗斯',
            '裕固', '乌孜别克', '门巴', '鄂伦春', '独龙', '赫哲', '高山', '珞巴', '塔塔尔'
        ]
        
        # 构建行政区划索引
        self._build_area_index()
    
    def _build_area_index(self):
        """构建行政区划索引"""
        for area in self.area_data:
            code = area['code']
            name = area['name']
            level = area['level']
            parent_code = area['parent_code']
            
            self.area_dict[code] = area
            
            if level == '1':  # 省级
                self.provinces.append(area)
            elif level == '2':  # 市级
                if parent_code not in self.cities:
                    self.cities[parent_code] = []
                self.cities[parent_code].append(area)
            elif level == '3':  # 区县级
                if parent_code not in self.counties:
                    self.counties[parent_code] = []
                self.counties[parent_code].append(area)
            elif level == '4':  # 街道/乡镇级
                if parent_code not in self.towns:
                    self.towns[parent_code] = []
                self.towns[parent_code].append(area)
    
    def get_random_birthdate(self, min_age=18, max_age=70):
        """
        生成随机出生日期
        
        Args:
            min_age: 最小年龄
            max_age: 最大年龄
            
        Returns:
            str: 出生日期字符串 (YYYYMMDD格式)
        """
        today = datetime.now()
        max_birthdate = today - timedelta(days=min_age*365)
        min_birthdate = today - timedelta(days=max_age*365)
        
        random_days = random.randint(0, (max_birthdate - min_birthdate).days)
        birthdate = min_birthdate + timedelta(days=random_days)
        
        return birthdate.strftime("%Y%m%d")
    
    def get_id_card_issue_date(self, birthdate_str):
        """
        根据出生日期生成符合逻辑的身份证起始日（签发日期）
        
        Args:
            birthdate_str: 出生日期字符串 (YYYYMMDD格式)
            
        Returns:
            tuple: (起始日期, 到期日期)
        """
        birthdate = datetime.strptime(birthdate_str, "%Y%m%d")
        birth_year = int(birthdate_str[:4])
        current_year = datetime.now().year
        age_at_issue = current_year - birth_year
        
        # 根据年龄确定起始日期逻辑
        if age_at_issue < 16:
            # 16岁以下，起始日期为16岁生日
            issue_date = birthdate.replace(year=birthdate.year + 16)
        else:
            # 随机在过去几年内签发
            issue_years_ago = random.randint(1, min(age_at_issue - 15, 10))
            issue_date = datetime.now() - timedelta(days=issue_years_ago*365)
        
        # 确保起始日期不早于16岁生日
        min_issue_date = birthdate.replace(year=birthdate.year + 16)
        if issue_date < min_issue_date:
            issue_date = min_issue_date
        
        # 确保起始日期不晚于当前日期
        if issue_date > datetime.now():
            issue_date = datetime.now() - timedelta(days=365)
        
        # 根据签发时的年龄确定有效期
        issue_age = issue_date.year - birthdate.year
        if issue_age < 16:
            expiry_years = 5  # 5年有效期
        elif issue_age < 25:
            expiry_years = 10  # 10年有效期
        elif issue_age < 46:
            expiry_years = 20  # 20年有效期
        else:
            expiry_years = 99  # 长期
        
        expiry_date = issue_date.replace(year=issue_date.year + expiry_years) if expiry_years < 99 else None
        
        # 格式化日期
        issue_date_str = issue_date.strftime("%Y.%m.%d")
        expiry_date_str = expiry_date.strftime("%Y.%m.%d") if expiry_years < 99 else "长期"
        
        return issue_date_str, expiry_date_str
    
    def generate_sequence_number(self, gender='random'):
        """
        生成顺序码（第15-17位）
        
        Args:
            gender: 性别 ('male', 'female', 'random')
            
        Returns:
            str: 3位顺序码
        """
        if gender == 'random':
            return f"{random.randint(0, 999):03d}"
        
        # 第17位奇数表示男性，偶数表示女性
        if gender == 'male':
            last_digit = random.choice([1, 3, 5, 7, 9])
        else:  # female
            last_digit = random.choice([0, 2, 4, 6, 8])
        
        first_two = random.randint(0, 99)
        return f"{first_two:02d}{last_digit}"
    
    def calculate_check_code(self, id_card_17):
        """
        计算身份证校验码（第18位）
        
        Args:
            id_card_17: 前17位身份证号码
            
        Returns:
            str: 校验码
        """
        # 加权因子
        factors = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
        # 校验码对应值
        check_codes = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']
        
        total = 0
        for i in range(17):
            total += int(id_card_17[i]) * factors[i]
        
        return check_codes[total % 11]
    
    def generate_house_number(self):
        """
        生成随机门牌号
        
        Returns:
            str: 门牌号，如"123号"
        """
        # 随机生成1-200之间的数字作为门牌号
        house_number = random.randint(1, 200)
        return f"{house_number}号"
    
    def generate_nation(self):
        """
        随机生成民族
        
        Returns:
            str: 民族名称
        """
        # 汉族占大多数，其他民族按一定比例分布
        if random.random() < 0.92:  # 约92%概率为汉族
            return '汉'
        else:
            # 从少数民族中随机选择
            minority_nations = [nation for nation in self.nations if nation != '汉']
            return random.choice(minority_nations)
    
    def generate_id_card(self, gender='random'):
        """
        生成单个身份证号码及国徽面信息
        
        Args:
            gender: 性别 ('male', 'female', 'random')
            
        Returns:
            dict: 包含身份证号码和国徽面信息的字典
        """
        # 1. 随机选择地区
        province_info = random.choice(self.provinces)
        available_cities = self.cities.get(province_info['code'], [])
        
        if available_cities:
            city_info = random.choice(available_cities)
            available_counties = self.counties.get(city_info['code'], [])
            if available_counties:
                county_info = random.choice(available_counties)
                area_code = county_info['code'][:6]
                
                # 尝试获取第四级街道地址
                available_towns = self.towns.get(county_info['code'], [])
                if available_towns:
                    town_info = random.choice(available_towns)
                else:
                    town_info = {'name': '', 'code': ''}
            else:
                area_code = city_info['code'][:6]
                county_info = {'name': '', 'code': ''}
                town_info = {'name': '', 'code': ''}
        else:
            area_code = province_info['code'][:6]
            city_info = {'name': '', 'code': ''}
            county_info = {'name': '', 'code': ''}
            town_info = {'name': '', 'code': ''}
        
        # 2. 生成出生日期
        birthdate = self.get_random_birthdate()
        
        # 3. 生成顺序码
        sequence = self.generate_sequence_number(gender)
        
        # 4. 组合前17位并计算校验码
        id_card_17 = area_code + birthdate + sequence
        check_code = self.calculate_check_code(id_card_17)
        
        # 5. 生成完整身份证号码
        id_card = id_card_17 + check_code
        
        # 6. 生成起始日期和到期日期
        issue_date, expiry_date = self.get_id_card_issue_date(birthdate)
        
        # 7. 构建详细地址信息（包含第四级街道和门牌号）
        address_parts = []
        if province_info:
            address_parts.append(province_info['name'])
        if city_info and city_info.get('name'):
            address_parts.append(city_info['name'])
        if county_info and county_info.get('name'):
            address_parts.append(county_info['name'])
        if town_info and town_info.get('name'):
            address_parts.append(town_info['name'])
        
        # 生成门牌号并添加到地址
        house_number = self.generate_house_number()
        full_address = ''.join(address_parts) + house_number
        
        # 8. 生成签发机关（通常是区县级公安局）
        issuing_authority = f"{county_info.get('name', city_info.get('name', province_info.get('name', '')))}公安局"
        
        # 9. 生成民族
        nation = self.generate_nation()
        
        return {
            # 身份证号码信息
            'id_card': id_card,
            'area_code': area_code,
            'birthdate': f"{birthdate[:4]}-{birthdate[4:6]}-{birthdate[6:8]}",
            'age': datetime.now().year - int(birthdate[:4]),
            'gender': '男' if int(sequence[2]) % 2 == 1 else '女',
            'nation': nation,  # 民族
            'province': province_info.get('name', ''),
            'city': city_info.get('name', ''),
            'county': county_info.get('name', ''),
            'town': town_info.get('name', ''),
            'house_number': house_number,
            'full_address': full_address,
            
            # 国徽面信息
            'issuing_authority': issuing_authority,  # 签发机关
            'issue_date': issue_date,  # 起始日期
            'expiry_date': expiry_date,  # 到期日期
        }
    
    def validate_id_card(self, id_card):
        """
        验证身份证号码是否合法
        
        Args:
            id_card: 身份证号码
            
        Returns:
            bool: 是否合法
        """
        if not re.match(r'^\d{17}[\dX]$', id_card):
            return False
        
        # 验证校验码
        check_code = self.calculate_check_code(id_card[:17])
        return check_code == id_card[17]

def load_area_data(file_path):
    """
    加载行政区划数据
    
    Args:
        file_path: JSON文件路径
        
    Returns:
        list: 行政区划数据
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"错误：找不到文件 {file_path}")
        return []
    except json.JSONDecodeError:
        print("错误：JSON文件格式不正确")
        return []

# 示例使用
if __name__ == "__main__":
    # 示例行政区划数据（包含第四级地址）
    sample_area_data = load_area_data('raw/area_2023.json');
    
    # 创建身份证生成器实例
    generator = IDCardGenerator(sample_area_data)
    
    # 生成单个身份证信息
    id_card_info = generator.generate_id_card()
    
    # 输出所有可用字段
    print("生成的身份证信息字段：")
    for key, value in id_card_info.items():
        print(f"{key}: {value}")
