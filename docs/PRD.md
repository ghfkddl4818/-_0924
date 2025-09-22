# Ultimate Automation System v2.0 - Complete Product Requirements Document

## 1. 프로젝트 개요

**프로젝트명**: Ultimate Automation System v2.0  
**목적**: 이커머스 제품 정보 수집 → 데이터 정리 → AI 콜드메일 생성 통합 자동화  
**대상 환경**: Windows 10/11, Python 3.10+, Chrome 브라우저, 1920x1080 해상도  
**인코딩**: UTF-8 (모든 파일)  

## 2. 핵심 요구사항

### 2.1 비즈니스 목표
- 매일 30개 이상의 이커머스 상품 정보를 안정적으로 수집
- 수집된 데이터를 기반으로 AI 콜드메일 초안 자동 생성
- 고객사 발굴 크롤링 결과를 CSV로 저장하여 영업팀 즉시 활용

### 2.2 기술 목표
- 하드코딩 제거, 모든 설정을 config.yaml로 외부화
- 강력한 에러 처리 및 자동 복구 메커니즘
- GUI 기반 실시간 모니터링 및 제어

## 3. 시스템 아키텍처

### 3.1 폴더 구조
```
ultimate_automation_system/
├── ultimate_automation_system.py    # 메인 GUI 및 통합 로직
├── config/
│   └── config.yaml                  # 모든 설정값
├── modules/
│   ├── __init__.py
│   ├── web_automation.py            # 웹 자동화 핵심 로직
│   ├── data_processor.py            # 파일 정리 및 DB 관리
│   ├── ai_generator.py              # OCR 및 LLM 콜드메일 생성
│   ├── image_matcher.py             # 향상된 이미지 매칭 유틸
│   └── error_handler.py             # 에러 복구 및 재시도 로직
├── assets/
│   ├── img/                         # 버튼 템플릿 이미지
│   │   ├── detail_button.png
│   │   ├── detail_button_alt.png    # 대체 이미지
│   │   ├── fireshot_save.png
│   │   ├── analysis_start.png
│   │   └── excel_download.png
│   └── templates/                   # 프롬프트 템플릿
│       └── cold_email_prompt.txt
├── data/
│   ├── work/                        # 임시 작업 폴더
│   ├── storage/                     # 정리된 데이터
│   │   └── ecommerce_database.xlsx
│   ├── cache/                       # 이미지 캐시
│   └── checkpoint/                  # 체크포인트 파일
├── downloads/                       # 원본 다운로드
│   ├── raw_images/
│   └── raw_reviews/
├── outputs/
│   ├── emails/                      # 생성된 콜드메일
│   ├── reports/                     # 일일 리포트
│   └── statistics/                  # 통계 데이터
├── logs/                            # 로그 파일
├── client_discovery/                # 고객사 발굴 모듈
│   ├── main_crawler.py
│   └── results/
├── requirements.txt                 # 의존성 패키지
└── README.md                        # 사용 가이드
```

### 3.2 모듈 구성

#### 메인 모듈 (ultimate_automation_system.py)
- Tkinter 기반 GUI 구현
- 6개 탭 구성: 현황, 웹 자동화, AI 생성, 결과, 설정, 고객사 발굴
- 비동기 작업 처리 (threading)
- 실시간 로그 및 진행률 표시

#### 웹 자동화 모듈 (modules/web_automation.py)
- 제품별 처리 플로우 관리
- 이미지 인식 기반 자동화
- 체크포인트 및 재시작 기능
- 연속 실패 감지 및 자동 중단

#### 이미지 매칭 모듈 (modules/image_matcher.py)
- 다중 스케일 검색 (0.8~1.2배)
- 그레이스케일 매칭
- 템플릿 캐싱
- 영역 제한 검색
- 대체 이미지 자동 시도

#### 데이터 처리 모듈 (modules/data_processor.py)
- 파일 자동 정리 및 이름 규칙 적용
- SHA-256 기반 중복 제거
- Excel DB 자동 업데이트
- 동적 시트/컬럼 매핑

#### AI 생성 모듈 (modules/ai_generator.py)
- EasyOCR/Tesseract 통합
- 영역별 OCR 수행
- LLM API 호출 (Gemini/OpenAI/Claude)
- 프롬프트 템플릿 적용
- 배치 처리 및 병렬화

#### 에러 처리 모듈 (modules/error_handler.py)
- 에러 타입별 복구 전략
- 자동 브라우저 재시작
- 지수 백오프 재시도
- 스킵 리스트 관리

## 4. 상세 설정 파일 (config.yaml)

```yaml
# Ultimate Automation System Configuration
# Version: 2.0.0
# Encoding: UTF-8

system:
  version: "2.0.0"
  encoding: "utf-8"
  debug_mode: false
  test_mode: false
  
paths:
  root_dir: "."  # 자동 감지
  download_folder: "./downloads"
  work_folder: "./data/work"
  storage_folder: "./data/storage"
  output_folder: "./outputs"
  log_folder: "./logs"
  checkpoint_folder: "./data/checkpoint"
  
database:
  file_path: "./data/storage/ecommerce_database.xlsx"
  sheet_name: "Products"
  backup_count: 5
  auto_save_interval: 10  # 10개 처리마다 자동 저장
  columns:
    - "수집일자"
    - "제품번호"
    - "제품명"
    - "브랜드명"
    - "가격"
    - "리뷰수"
    - "평점"
    - "처리상태"
    - "이메일생성"
    - "비고"
  
web_automation:
  total_products: 30
  browser: "chrome"
  window_state: "maximized"
  zoom_level: 100
  tab_switch_delay: 0.5
  
  # 이미지 매칭 설정
  image_matching:
    confidence: 0.8
    grayscale: true
    multi_scale: [0.8, 0.9, 1.0, 1.1, 1.2]
    region_limit: true
    cache_templates: true
    match_method: "cv2.TM_CCOEFF_NORMED"
    
  # 각 버튼별 상세 설정
  buttons:
    detail:
      primary: "assets/img/detail_button.png"
      alternative: "assets/img/detail_button_alt.png"
      confidence: 0.85
      retry: 5
      wait_after: 2.0
      search_region: [0, 200, 1920, 800]
      click_offset: [0, 0]
      
    fireshot:
      trigger_key: "ctrl+shift+s"
      save_button: "assets/img/fireshot_save.png"
      confidence: 0.9
      timeout: 5.0
      wait_after: 3.0
      
    analysis:
      start: "assets/img/analysis_start.png"
      excel: "assets/img/excel_download.png"
      confidence: 0.85
      wait_between: 1.5
      download_timeout: 10.0
      
    navigation:
      next_tab: "ctrl+tab"
      prev_tab: "ctrl+shift+tab"
      close_tab: "ctrl+w"
      
  # 스크롤 설정
  scrolling:
    amount: 500
    max_scrolls: 16
    wait_between: 0.5
    smooth_scroll: true
    
  # 에러 처리
  error_handling:
    retry_attempts: 3
    retry_delay: 1.0
    fail_fast_limit: 3
    consecutive_fail_action: "pause"  # pause, skip, restart
    auto_restart_browser: true
    checkpoint_enabled: true
    checkpoint_interval: 5  # 5개마다 저장
    skip_list_file: "./data/skip_list.txt"
    
ocr:
  engine: "easyocr"  # tesseract, easyocr
  languages: ["ko", "en"]
  gpu: false
  
  # 영역별 OCR 설정 (x, y, width, height)
  regions:
    product_name: [100, 50, 800, 150]
    price: [100, 200, 300, 250]
    brand: [100, 300, 500, 350]
    description: [100, 400, 1000, 500]
    
  # 전처리 옵션
  preprocessing:
    grayscale: true
    denoise: true
    threshold: 128
    dpi: 300
    
  # EasyOCR 설정
  easyocr:
    detail: 1  # 0: simple, 1: detailed
    paragraph: true
    width_ths: 0.5
    
  # Tesseract 설정
  tesseract:
    psm: 3  # Page Segmentation Mode
    oem: 3  # OCR Engine Mode
    config: "--oem 3 --psm 3 -l kor+eng"
    
ai:
  provider: "gemini"  # gemini, openai, claude
  api_key: "${GEMINI_API_KEY}"  # 환경변수에서 읽기
  
  # 모델별 설정
  models:
    gemini:
      model: "gemini-1.5-flash"
      temperature: 0.7
      max_tokens: 1000
      top_p: 0.9
      
    openai:
      model: "gpt-4"
      temperature: 0.7
      max_tokens: 1000
      
    claude:
      model: "claude-3-sonnet"
      temperature: 0.7
      max_tokens: 1000
      
  # 생성 설정
  generation:
    retry_attempts: 3
    timeout: 30
    exponential_backoff: true
    batch_size: 5
    
  # 프롬프트 설정
  prompt:
    template_file: "assets/templates/cold_email_prompt.txt"
    tone: "professional"  # professional, casual, friendly
    language: "korean"
    max_length: 500
    must_include:
      - "product_name"
      - "unique_features"
      - "call_to_action"
    optional_include:
      - "price_mention"
      - "review_summary"
      
gui:
  window:
    title: "Ultimate Automation System v2.0"
    size: "1400x800"
    min_size: "1200x600"
    resizable: true
    theme: "modern"  # classic, modern, dark
    icon: "assets/icon.ico"
    
  # 탭 설정
  tabs:
    overview:
      name: "현황"
      icon: "📊"
      enabled: true
      
    web_automation:
      name: "웹 자동화"
      icon: "🌐"
      enabled: true
      
    ai_generation:
      name: "AI 생성"
      icon: "🤖"
      enabled: true
      
    results:
      name: "결과"
      icon: "📁"
      enabled: true
      
    settings:
      name: "설정"
      icon: "⚙️"
      enabled: true
      
    client_discovery:
      name: "고객사 발굴"
      icon: "🔍"
      enabled: false  # 선택적 기능
      
  # 단축키
  shortcuts:
    start: "F5"
    stop: "Escape"
    pause: "F6"
    resume: "F7"
    settings: "F12"
    
  # 알림 설정
  notifications:
    sound_enabled: true
    sound_file: "assets/sounds/notification.wav"
    popup_enabled: true
    popup_duration: 5
    system_tray: true
    
  # 색상 테마
  colors:
    modern:
      background: "#f0f0f0"
      foreground: "#333333"
      accent: "#007acc"
      success: "#28a745"
      warning: "#ffc107"
      error: "#dc3545"
      
performance:
  batch_size: 10
  memory_limit_mb: 2048
  gc_interval: 50  # 50개 처리마다 가비지 컬렉션
  parallel_ocr: true
  max_workers: 4
  cache_size_mb: 512
  
  # 최적화 옵션
  optimization:
    lazy_loading: true
    image_compression: true
    result_pagination: true
    
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
  format: "[%(asctime)s][%(name)s][%(levelname)s] %(message)s"
  date_format: "%Y-%m-%d %H:%M:%S"
  file_rotation: "daily"
  max_files: 30
  max_size_mb: 100
  console_output: true
  gui_output: true
  
  # 로그 레벨별 설정
  levels:
    DEBUG:
      file: true
      console: false
      gui: false
      
    INFO:
      file: true
      console: true
      gui: true
      
    WARNING:
      file: true
      console: true
      gui: true
      popup: false
      
    ERROR:
      file: true
      console: true
      gui: true
      popup: true
      
    CRITICAL:
      file: true
      console: true
      gui: true
      popup: true
      sound: true
      
monitoring:
  statistics:
    enabled: true
    export_format: "json"  # json, csv, excel
    export_interval: 3600  # 1시간마다
    dashboard: true
    
  # 통계 항목
  metrics:
    - "total_processed"
    - "success_rate"
    - "average_time"
    - "error_count"
    - "skip_count"
    
  # 알림 조건
  alerts:
    email: false
    email_to: ""
    slack: false
    slack_webhook: ""
    threshold_success_rate: 0.8
    threshold_error_count: 10
    
client_discovery:
  enabled: false
  crawler_module: "./client_discovery/main_crawler.py"
  
  # 크롤링 설정
  crawling:
    platform: "naver"  # naver, coupang, gmarket
    max_pages: 10
    delay_between_requests: 1.0
    user_agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
  # 필터 조건
  filters:
    review_min: 100
    review_max: 10000
    interest_min: 50
    interest_max: 5000
    rating_min: 4.0
    
  # 출력 설정
  output:
    format: "csv"  # csv, json, excel
    fields:
      - "company_name"
      - "product_name"
      - "review_count"
      - "interest_count"
      - "rating"
      - "url"
      - "contact"
```

## 5. 핵심 모듈 구현 상세

### 5.1 메인 모듈 구조

```python
# ultimate_automation_system.py

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import yaml
import logging
from pathlib import Path
from datetime import datetime
from modules import (
    WebAutomation, 
    DataProcessor, 
    AIGenerator,
    EnhancedImageMatcher,
    ErrorHandler
)

class UltimateAutomationSystem:
    """
    통합 자동화 시스템 메인 클래스
    """
    
    def __init__(self):
        # 설정 로드 및 검증
        self.config = self.load_config()
        self.validate_environment()
        
        # GUI 초기화
        self.root = tk.Tk()
        self.setup_gui()
        self.setup_tabs()
        self.setup_logging()
        
        # 상태 관리
        self.state = {
            'running': False,
            'paused': False,
            'current_step': None,
            'current_product': 0,
            'total_products': self.config['web_automation']['total_products'],
            'progress': 0,
            'success_count': 0,
            'fail_count': 0,
            'skip_count': 0,
            'skip_list': set(),
            'start_time': None,
            'checkpoint': None
        }
        
        # 모듈 초기화
        self.web_automation = WebAutomation(self.config, self.log_callback)
        self.data_processor = DataProcessor(self.config, self.log_callback)
        self.ai_generator = AIGenerator(self.config, self.log_callback)
        self.error_handler = ErrorHandler(self.config, self.log_callback)
        
        # 스레드 관리
        self.automation_thread = None
        self.stop_event = threading.Event()
        
    def load_config(self):
        """설정 파일 로드 및 환경변수 처리"""
        config_path = Path("config/config.yaml")
        
        if not config_path.exists():
            self.create_default_config()
            
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            
        # 환경변수 치환
        self.replace_env_vars(config)
        
        # 경로 절대경로 변환
        self.resolve_paths(config)
        
        return config
        
    def validate_environment(self):
        """실행 환경 검증"""
        # 필수 폴더 생성
        folders = [
            'data/work', 'data/storage', 'data/cache', 'data/checkpoint',
            'downloads/raw_images', 'downloads/raw_reviews',
            'outputs/emails', 'outputs/reports', 'outputs/statistics',
            'logs', 'assets/img', 'assets/templates'
        ]
        
        for folder in folders:
            Path(folder).mkdir(parents=True, exist_ok=True)
            
        # 이미지 템플릿 확인
        required_images = [
            'detail_button.png', 'fireshot_save.png',
            'analysis_start.png', 'excel_download.png'
        ]
        
        missing = []
        for img in required_images:
            if not Path(f"assets/img/{img}").exists():
                missing.append(img)
                
        if missing:
            self.log("WARNING", f"Missing template images: {missing}")
            
    def setup_gui(self):
        """GUI 메인 윈도우 설정"""
        # 윈도우 설정
        self.root.title(self.config['gui']['window']['title'])
        self.root.geometry(self.config['gui']['window']['size'])
        
        # 메인 프레임
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 상단 컨트롤 패널
        self.setup_control_panel(main_frame)
        
        # 탭 컨테이너
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
    def setup_control_panel(self, parent):
        """상단 컨트롤 패널 구성"""
        control_frame = ttk.LabelFrame(parent, text="메인 컨트롤", padding=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 상태 표시
        self.status_label = ttk.Label(
            control_frame, 
            text="대기 중", 
            font=('Arial', 12, 'bold')
        )
        self.status_label.grid(row=0, column=0, padx=10)
        
        # 진행률
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            control_frame, 
            variable=self.progress_var,
            maximum=100,
            length=300
        )
        self.progress_bar.grid(row=0, column=1, padx=10)
        
        self.progress_label = ttk.Label(control_frame, text="0/30")
        self.progress_label.grid(row=0, column=2, padx=5)
        
        # 버튼들
        self.start_button = ttk.Button(
            control_frame,
            text="▶ 시작 (F5)",
            command=self.start_automation,
            width=15
        )
        self.start_button.grid(row=0, column=3, padx=5)
        
        self.pause_button = ttk.Button(
            control_frame,
            text="⏸ 일시정지",
            command=self.pause_automation,
            width=15,
            state=tk.DISABLED
        )
        self.pause_button.grid(row=0, column=4, padx=5)
        
        self.stop_button = ttk.Button(
            control_frame,
            text="⏹ 중단 (ESC)",
            command=self.stop_automation,
            width=15,
            state=tk.DISABLED
        )
        self.stop_button.grid(row=0, column=5, padx=5)
        
        # 통계
        stats_frame = ttk.Frame(control_frame)
        stats_frame.grid(row=1, column=0, columnspan=6, pady=10)
        
        self.stats_label = ttk.Label(
            stats_frame,
            text="성공: 0 | 실패: 0 | 스킵: 0 | 소요시간: 00:00:00"
        )
        self.stats_label.pack()
        
    def setup_tabs(self):
        """탭 구성"""
        # 1. 현황 탭
        self.overview_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.overview_tab, text="📊 현황")
        self.setup_overview_tab()
        
        # 2. 웹 자동화 탭
        self.web_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.web_tab, text="🌐 웹 자동화")
        self.setup_web_automation_tab()
        
        # 3. AI 생성 탭
        self.ai_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.ai_tab, text="🤖 AI 생성")
        self.setup_ai_generation_tab()
        
        # 4. 결과 탭
        self.results_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.results_tab, text="📁 결과")
        self.setup_results_tab()
        
        # 5. 설정 탭
        self.settings_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_tab, text="⚙️ 설정")
        self.setup_settings_tab()
        
        # 6. 고객사 발굴 탭 (선택적)
        if self.config['client_discovery']['enabled']:
            self.discovery_tab = ttk.Frame(self.notebook)
            self.notebook.add(self.discovery_tab, text="🔍 고객사 발굴")
            self.setup_discovery_tab()
```

### 5.2 웹 자동화 모듈

```python
# modules/web_automation.py

import pyautogui
import time
import json
from pathlib import Path
from typing import Callable, Optional, Tuple
from .image_matcher import EnhancedImageMatcher
from .error_handler import ErrorHandler

class WebAutomation:
    """웹 자동화 핵심 모듈"""
    
    def __init__(self, config: dict, log_callback: Callable):
        self.config = config
        self.log = log_callback
        self.matcher = EnhancedImageMatcher(config)
        self.error_handler = ErrorHandler(config, log_callback)
        
        # 체크포인트 관리
        self.checkpoint_file = Path(config['paths']['checkpoint_folder']) / "checkpoint.json"
        self.checkpoint_data = self.load_checkpoint()
        
        # 상태 추적
        self.consecutive_failures = 0
        self.processed_count = 0
        self.skip_list = set()
        
    def process_all_products(self, start_index: int = 0) -> dict:
        """
        모든 제품 처리 메인 루프
        
        Returns:
            dict: 처리 결과 통계
        """
        total = self.config['web_automation']['total_products']
        results = {'success': 0, 'failed': 0, 'skipped': 0}
        
        # 체크포인트에서 재개
        if self.checkpoint_data and not start_index:
            start_index = self.checkpoint_data.get('last_processed', 0) + 1
            self.log("INFO", f"체크포인트에서 재개: 제품 {start_index}부터 시작")
            
        for index in range(start_index, total):
            # 스킵 리스트 확인
            if index in self.skip_list:
                self.log("INFO", f"제품 {index+1} 스킵 (스킵 리스트)")
                results['skipped'] += 1
                continue
                
            try:
                # 단일 제품 처리
                success = self.process_single_product(index)
                
                if success:
                    results['success'] += 1
                    self.consecutive_failures = 0
                    self.log("SUCCESS", f"제품 {index+1}/{total} 처리 완료")
                else:
                    results['failed'] += 1
                    self.consecutive_failures += 1
                    self.log("ERROR", f"제품 {index+1}/{total} 처리 실패")
                    
                    # 연속 실패 확인
                    if self.consecutive_failures >= self.config['web_automation']['error_handling']['fail_fast_limit']:
                        self.handle_consecutive_failures()
                        break
                        
                # 체크포인트 저장
                if (index + 1) % self.config['web_automation']['error_handling']['checkpoint_interval'] == 0:
                    self.save_checkpoint(index)
                    
                # 다음 탭으로 이동
                pyautogui.hotkey('ctrl', 'tab')
                time.sleep(self.config['web_automation']['tab_switch_delay'])
                
            except Exception as e:
                self.log("ERROR", f"예외 발생: {str(e)}")
                results['failed'] += 1
                
        return results
        
    def process_single_product(self, index: int) -> bool:
        """
        단일 제품 처리 플로우
        
        Args:
            index: 제품 인덱스 (0부터 시작)
            
        Returns:
            bool: 성공 여부
        """
        self.log("INFO", f"제품 {index+1} 처리 시작")
        
        # Step 1: 상세보기 클릭
        if not self.click_detail_button():
            return False
            
        # Step 2: Fireshot 캡처
        if not self.capture_with_fireshot():
            return False
            
        # Step 3: 리뷰 데이터 다운로드
        if not self.download_review_data():
            return False
            
        # Step 4: 추가 데이터 수집 (선택적)
        self.collect_additional_data()
        
        return True
        
    def click_detail_button(self) -> bool:
        """상세보기 버튼 클릭"""
        button_config = self.config['web_automation']['buttons']['detail']
        
        # 메인 이미지로 시도
        result = self.matcher.find_and_click(
            button_config['primary'],
            confidence=button_config['confidence'],
            retry=button_config['retry'],
            region=button_config.get('search_region'),
            wait_after=button_config['wait_after']
        )
        
        # 실패 시 대체 이미지로 시도
        if not result and button_config.get('alternative'):
            self.log("WARNING", "메인 이미지 실패, 대체 이미지로 시도")
            result = self.matcher.find_and_click(
                button_config['alternative'],
                confidence=button_config['confidence'] * 0.9,
                retry=3
            )
            
        return result
        
    def capture_with_fireshot(self) -> bool:
        """Fireshot으로 페이지 캡처"""
        try:
            # Fireshot 단축키 실행
            pyautogui.hotkey(*self.config['web_automation']['buttons']['fireshot']['trigger_key'].split('+'))
            time.sleep(1)
            
            # 저장 버튼 클릭
            save_button = self.config['web_automation']['buttons']['fireshot']['save_button']
            result = self.matcher.find_and_click(
                save_button,
                confidence=self.config['web_automation']['buttons']['fireshot']['confidence'],
                timeout=self.config['web_automation']['buttons']['fireshot']['timeout']
            )
            
            if result:
                time.sleep(self.config['web_automation']['buttons']['fireshot']['wait_after'])
                self.log("SUCCESS", "Fireshot 캡처 완료")
                
            return result
            
        except Exception as e:
            self.log("ERROR", f"Fireshot 캡처 실패: {str(e)}")
            return False
            
    def download_review_data(self) -> bool:
        """리뷰 데이터 Excel 다운로드"""
        try:
            # 분석 시작 버튼
            if not self.matcher.find_and_click(
                self.config['web_automation']['buttons']['analysis']['start'],
                confidence=self.config['web_automation']['buttons']['analysis']['confidence']
            ):
                return False
                
            time.sleep(self.config['web_automation']['buttons']['analysis']['wait_between'])
            
            # Excel 다운로드 버튼
            if not self.matcher.find_and_click(
                self.config['web_automation']['buttons']['analysis']['excel'],
                confidence=self.config['web_automation']['buttons']['analysis']['confidence']
            ):
                return False
                
            # 다운로드 완료 대기
            time.sleep(self.config['web_automation']['buttons']['analysis']['download_timeout'])
            self.log("SUCCESS", "리뷰 데이터 다운로드 완료")
            return True
            
        except Exception as e:
            self.log("ERROR", f"리뷰 다운로드 실패: {str(e)}")
            return False
```

### 5.3 이미지 매칭 모듈

```python
# modules/image_matcher.py

import cv2
import numpy as np
import pyautogui
from typing import Optional, Tuple, List
from pathlib import Path
import time

class EnhancedImageMatcher:
    """향상된 이미지 매칭 모듈"""
    
    def __init__(self, config: dict):
        self.config = config
        self.template_cache = {}
        self.last_positions = {}
        
        # PyAutoGUI 설정
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1
        
    def find_and_click(
        self,
        template_path: str,
        confidence: float = None,
        region: Optional[List[int]] = None,
        grayscale: bool = None,
        scales: Optional[List[float]] = None,
        retry: int = 3,
        timeout: float = 10,
        wait_after: float = 0.5,
        click_offset: Tuple[int, int] = (0, 0)
    ) -> bool:
        """
        이미지를 찾고 클릭하는 통합 메서드
        
        Args:
            template_path: 템플릿 이미지 경로
            confidence: 매칭 신뢰도
            region: 검색 영역 [x, y, width, height]
            grayscale: 그레이스케일 변환 여부
            scales: 다중 스케일 리스트
            retry: 재시도 횟수
            timeout: 타임아웃 (초)
            wait_after: 클릭 후 대기 시간
            click_offset: 클릭 위치 오프셋
            
        Returns:
            bool: 성공 여부
        """
        # 기본값 설정
        if confidence is None:
            confidence = self.config['web_automation']['image_matching']['confidence']
        if grayscale is None:
            grayscale = self.config['web_automation']['image_matching']['grayscale']
        if scales is None:
            scales = self.config['web_automation']['image_matching'].get('multi_scale', [1.0])
            
        # 템플릿 로드 (캐시 활용)
        template = self.load_template(template_path)
        if template is None:
            return False
            
        start_time = time.time()
        attempt = 0
        
        while attempt < retry and (time.time() - start_time) < timeout:
            # 다중 스케일 검색
            for scale in scales:
                position = self.find_image(
                    template,
                    confidence=confidence,
                    region=region,
                    grayscale=grayscale,
                    scale=scale
                )
                
                if position:
                    # 클릭
                    click_x = position[0] + click_offset[0]
                    click_y = position[1] + click_offset[1]
                    pyautogui.click(click_x, click_y)
                    
                    # 위치 캐시 저장
                    self.last_positions[template_path] = position
                    
                    # 클릭 후 대기
                    time.sleep(wait_after)
                    return True
                    
            attempt += 1
            time.sleep(0.5)
            
        return False
        
    def find_image(
        self,
        template: np.ndarray,
        confidence: float = 0.8,
        region: Optional[List[int]] = None,
        grayscale: bool = True,
        scale: float = 1.0
    ) -> Optional[Tuple[int, int]]:
        """
        화면에서 이미지 찾기
        
        Returns:
            Optional[Tuple[int, int]]: 찾은 위치 (x, y) 또는 None
        """
        try:
            # 스크린샷 캡처
            if region:
                screenshot = pyautogui.screenshot(region=tuple(region))
            else:
                screenshot = pyautogui.screenshot()
                
            # OpenCV 형식으로 변환
            screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            # 그레이스케일 변환
            if grayscale:
                screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
                template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY) if len(template.shape) == 3 else template
            else:
                template_gray = template
                
            # 스케일 조정
            if scale != 1.0:
                width = int(template_gray.shape[1] * scale)
                height = int(template_gray.shape[0] * scale)
                template_scaled = cv2.resize(template_gray, (width, height))
            else:
                template_scaled = template_gray
                
            # 템플릿 매칭
            result = cv2.matchTemplate(
                screenshot,
                template_scaled,
                cv2.TM_CCOEFF_NORMED
            )
            
            # 최대값 찾기
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= confidence:
                # 중심점 계산
                center_x = max_loc[0] + template_scaled.shape[1] // 2
                center_y = max_loc[1] + template_scaled.shape[0] // 2
                
                # region 오프셋 추가
                if region:
                    center_x += region[0]
                    center_y += region[1]
                    
                return (center_x, center_y)
                
        except Exception as e:
            print(f"이미지 매칭 오류: {str(e)}")
            
        return None
        
    def load_template(self, template_path: str) -> Optional[np.ndarray]:
        """
        템플릿 이미지 로드 (캐시 활용)
        
        Args:
            template_path: 템플릿 이미지 경로
            
        Returns:
            Optional[np.ndarray]: 로드된 이미지 또는 None
        """
        # 캐시 확인
        if template_path in self.template_cache:
            return self.template_cache[template_path]
            
        # 파일 존재 확인
        path = Path(template_path)
        if not path.exists():
            print(f"템플릿 이미지를 찾을 수 없음: {template_path}")
            return None
            
        # 이미지 로드
        try:
            template = cv2.imread(str(path))
            
            # 캐시 저장
            if self.config['web_automation']['image_matching'].get('cache_templates', True):
                self.template_cache[template_path] = template
                
            return template
            
        except Exception as e:
            print(f"템플릿 로드 오류: {str(e)}")
            return None
```

### 5.4 데이터 처리 모듈

```python
# modules/data_processor.py

import pandas as pd
import shutil
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

class DataProcessor:
    """데이터 정리 및 DB 관리 모듈"""
    
    def __init__(self, config: dict, log_callback):
        self.config = config
        self.log = log_callback
        self.db_manager = ExcelDBManager(
            config['database']['file_path'],
            config['database']['sheet_name'],
            log_callback
        )
        self.hash_cache = {}
        
    def organize_files(self, date: Optional[str] = None) -> Dict[str, int]:
        """
        다운로드된 파일 정리
        
        Args:
            date: 날짜 문자열 (YYYY-MM-DD)
            
        Returns:
            Dict[str, int]: 정리 결과 통계
        """
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
            
        results = {
            'images_processed': 0,
            'reviews_processed': 0,
            'duplicates_removed': 0,
            'errors': 0
        }
        
        # 이미지 파일 정리
        image_count = self.organize_images(date)
        results['images_processed'] = image_count
        
        # 리뷰 파일 정리
        review_count = self.organize_reviews(date)
        results['reviews_processed'] = review_count
        
        # 중복 제거
        duplicates = self.remove_duplicates()
        results['duplicates_removed'] = duplicates
        
        self.log("INFO", f"파일 정리 완료: {results}")
        
        return results
        
    def organize_images(self, date: str) -> int:
        """이미지 파일 정리"""
        source_dir = Path(self.config['paths']['download_folder'])
        target_dir = Path(self.config['paths']['storage_folder']) / 'images' / date
        target_dir.mkdir(parents=True, exist_ok=True)
        
        count = 0
        for img_file in source_dir.glob("*.png"):
            # 파일명 규칙 적용
            new_name = f"product_{count+1:03d}_{date}.png"
            target_path = target_dir / new_name
            
            # 중복 확인
            if not self.is_duplicate(img_file, target_path):
                shutil.move(str(img_file), str(target_path))
                count += 1
                self.log("DEBUG", f"이미지 이동: {img_file.name} → {new_name}")
                
        return count
        
    def organize_reviews(self, date: str) -> int:
        """리뷰 Excel 파일 정리"""
        source_dir = Path(self.config['paths']['download_folder'])
        target_dir = Path(self.config['paths']['storage_folder']) / 'reviews' / date
        target_dir.mkdir(parents=True, exist_ok=True)
        
        count = 0
        for excel_file in source_dir.glob("*.xlsx"):
            new_name = f"review_{count+1:03d}_{date}.xlsx"
            target_path = target_dir / new_name
            
            if not self.is_duplicate(excel_file, target_path):
                shutil.move(str(excel_file), str(target_path))
                count += 1
                self.log("DEBUG", f"리뷰 이동: {excel_file.name} → {new_name}")
                
        return count
        
    def is_duplicate(self, source: Path, target: Path) -> bool:
        """SHA-256 해시로 중복 확인"""
        if not target.exists():
            return False
            
        source_hash = self.get_file_hash(source)
        target_hash = self.get_file_hash(target)
        
        return source_hash == target_hash
        
    def get_file_hash(self, file_path: Path) -> str:
        """파일 해시 계산 (캐시 활용)"""
        # 캐시 확인
        str_path = str(file_path)
        if str_path in self.hash_cache:
            return self.hash_cache[str_path]
            
        # 해시 계산
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hasher.update(chunk)
                
        file_hash = hasher.hexdigest()
        self.hash_cache[str_path] = file_hash
        
        return file_hash
        
    def update_database(self, product_data: Dict) -> bool:
        """데이터베이스 업데이트"""
        try:
            return self.db_manager.add_product(product_data)
        except Exception as e:
            self.log("ERROR", f"DB 업데이트 실패: {str(e)}")
            return False

class ExcelDBManager:
    """Excel 데이터베이스 관리 클래스"""
    
    def __init__(self, db_path: str, sheet_name: str, log_callback):
        self.db_path = Path(db_path)
        self.sheet_name = sheet_name
        self.log = log_callback
        self.ensure_database()
        
    def ensure_database(self):
        """데이터베이스 파일 확인 및 생성"""
        if not self.db_path.exists():
            # 새 데이터베이스 생성
            columns = [
                '수집일자', '제품번호', '제품명', '브랜드명', 
                '가격', '리뷰수', '평점', '처리상태', 
                '이메일생성', '비고'
            ]
            df = pd.DataFrame(columns=columns)
            df.to_excel(self.db_path, sheet_name=self.sheet_name, index=False)
            self.log("INFO", f"새 데이터베이스 생성: {self.db_path}")
            
    def add_product(self, product_data: Dict) -> bool:
        """제품 데이터 추가"""
        try:
            # 기존 데이터 로드
            df = pd.read_excel(self.db_path, sheet_name=self.sheet_name)
            
            # 새 데이터 추가
            new_row = pd.DataFrame([product_data])
            df = pd.concat([df, new_row], ignore_index=True)
            
            # 저장
            df.to_excel(self.db_path, sheet_name=self.sheet_name, index=False)
            
            # 백업 생성
            if len(df) % 10 == 0:
                self.create_backup()
                
            return True
            
        except Exception as e:
            self.log("ERROR", f"제품 추가 실패: {str(e)}")
            return False
            
    def create_backup(self):
        """데이터베이스 백업 생성"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.db_path.parent / f"backup_{timestamp}_{self.db_path.name}"
        shutil.copy(self.db_path, backup_path)
        self.log("INFO", f"백업 생성: {backup_path.name}")
```

### 5.5 AI 생성 모듈

```python
# modules/ai_generator.py

import easyocr
import google.generativeai as genai
from pathlib import Path
from typing import List, Dict, Optional
import json
import time

class AIGenerator:
    """AI 기반 콜드메일 생성 모듈"""
    
    def __init__(self, config: dict, log_callback):
        self.config = config
        self.log = log_callback
        
        # OCR 엔진 초기화
        self.ocr_engine = self._setup_ocr()
        
        # LLM 클라이언트 초기화
        self.llm_client = self._setup_llm()
        
        # 프롬프트 템플릿 로드
        self.prompt_template = self._load_prompt_template()
        
    def _setup_ocr(self):
        """OCR 엔진 설정"""
        if self.config['ocr']['engine'] == 'easyocr':
            return easyocr.Reader(
                self.config['ocr']['languages'],
                gpu=self.config['ocr']['gpu']
            )
        else:
            # Tesseract 설정
            import pytesseract
            return pytesseract
            
    def _setup_llm(self):
        """LLM 클라이언트 설정"""
        provider = self.config['ai']['provider']
        
        if provider == 'gemini':
            genai.configure(api_key=self.config['ai']['api_key'])
            return genai.GenerativeModel(
                self.config['ai']['models']['gemini']['model']
            )
        elif provider == 'openai':
            import openai
            openai.api_key = self.config['ai']['api_key']
            return openai
        else:
            raise ValueError(f"지원되지 않는 AI 제공자: {provider}")
            
    def _load_prompt_template(self) -> str:
        """프롬프트 템플릿 로드"""
        template_path = Path(self.config['ai']['prompt']['template_file'])
        
        if template_path.exists():
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            # 기본 템플릿
            return """
            다음 제품 정보를 바탕으로 B2B 콜드메일을 작성해주세요:
            
            제품명: {product_name}
            브랜드: {brand}
            특징: {features}
            리뷰 요약: {review_summary}
            
            요구사항:
            - 톤: {tone}
            - 언어: {language}
            - 필수 포함: {must_include}
            - 최대 길이: {max_length}자
            
            메일 작성:
            """
            
    def generate_cold_emails(
        self,
        product_data_list: List[Dict]
    ) -> List[Dict]:
        """
        여러 제품에 대한 콜드메일 생성
        
        Args:
            product_data_list: 제품 정보 리스트
            
        Returns:
            List[Dict]: 생성된 이메일 리스트
        """
        results = []
        batch_size = self.config['ai']['generation']['batch_size']
        
        # 배치 처리
        for i in range(0, len(product_data_list), batch_size):
            batch = product_data_list[i:i+batch_size]
            
            for product_data in batch:
                try:
                    email = self.generate_single_email(product_data)
                    results.append({
                        'product_id': product_data['id'],
                        'email': email,
                        'status': 'success'
                    })
                    self.log("SUCCESS", f"이메일 생성 완료: {product_data['name']}")
                    
                except Exception as e:
                    results.append({
                        'product_id': product_data['id'],
                        'error': str(e),
                        'status': 'failed'
                    })
                    self.log("ERROR", f"이메일 생성 실패: {str(e)}")
                    
                # API 제한 대응
                time.sleep(1)
                
        return results
        
    def generate_single_email(self, product_data: Dict) -> str:
        """
        단일 제품에 대한 콜드메일 생성
        
        Args:
            product_data: 제품 정보
            
        Returns:
            str: 생성된 이메일 내용
        """
        # OCR로 추가 정보 추출
        if 'image_path' in product_data:
            ocr_text = self.extract_text_from_image(product_data['image_path'])
            product_data['ocr_features'] = ocr_text
            
        # 프롬프트 생성
        prompt = self.create_prompt(product_data)
        
        # LLM 호출 (재시도 포함)
        max_retries = self.config['ai']['generation']['retry_attempts']
        
        for attempt in range(max_retries):
            try:
                response = self.call_llm(prompt)
                
                # 품질 검증
                if self.validate_email(response):
                    return response
                    
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                    
                # 지수 백오프
                wait_time = 2 ** attempt
                self.log("WARNING", f"LLM 호출 재시도 ({attempt+1}/{max_retries}), {wait_time}초 대기")
                time.sleep(wait_time)
                
        raise ValueError("유효한 이메일 생성 실패")
        
    def extract_text_from_image(
        self,
        image_path: str,
        regions: Optional[List[List[int]]] = None
    ) -> Dict[str, str]:
        """
        이미지에서 텍스트 추출
        
        Args:
            image_path: 이미지 파일 경로
            regions: OCR 수행할 영역 리스트
            
        Returns:
            Dict[str, str]: 영역별 추출된 텍스트
        """
        results = {}
        
        if self.config['ocr']['engine'] == 'easyocr':
            # EasyOCR 사용
            ocr_results = self.ocr_engine.readtext(image_path)
            
            # 영역별 필터링
            if regions:
                for region_name, region_coords in self.config['ocr']['regions'].items():
                    region_text = self._filter_ocr_by_region(
                        ocr_results,
                        region_coords
                    )
                    results[region_name] = region_text
            else:
                # 전체 텍스트
                full_text = ' '.join([text[1] for text in ocr_results])
                results['full_text'] = full_text
                
        return results
        
    def call_llm(self, prompt: str) -> str:
        """LLM API 호출"""
        provider = self.config['ai']['provider']
        
        if provider == 'gemini':
            response = self.llm_client.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=self.config['ai']['models']['gemini']['temperature'],
                    max_output_tokens=self.config['ai']['models']['gemini']['max_tokens']
                )
            )
            return response.text
            
        # 다른 제공자 처리...
        
    def validate_email(self, email_content: str) -> bool:
        """생성된 이메일 품질 검증"""
        # 필수 요소 확인
        must_include = self.config['ai']['prompt']['must_include']
        
        for element in must_include:
            if element not in email_content.lower():
                self.log("WARNING", f"필수 요소 누락: {element}")
                return False
                
        # 길이 확인
        max_length = self.config['ai']['prompt'].get('max_length', 1000)
        if len(email_content) > max_length:
            self.log("WARNING", f"이메일 길이 초과: {len(email_content)} > {max_length}")
            return False
            
        return True
```

## 6. 에러 처리 및 복구 전략

```python
# modules/error_handler.py

from enum import Enum
from typing import Dict, Callable, Optional
import time
import subprocess

class ErrorType(Enum):
    """에러 타입 정의"""
    IMAGE_NOT_FOUND = "image_not_found"
    DOWNLOAD_FAILED = "download_failed"
    BROWSER_HANG = "browser_hang"
    LLM_TIMEOUT = "llm_timeout"
    FILE_ACCESS_ERROR = "file_access_error"
    NETWORK_ERROR = "network_error"

class ErrorHandler:
    """통합 에러 처리 및 복구 시스템"""
    
    # 에러 타입별 처리 전략
    ERROR_STRATEGIES = {
        ErrorType.IMAGE_NOT_FOUND: {
            'retry': 3,
            'action': 'retry_with_alt_image',
            'log_level': 'WARNING',
            'wait': 1.0
        },
        ErrorType.DOWNLOAD_FAILED: {
            'retry': 2,
            'action': 'wait_and_retry',
            'log_level': 'ERROR',
            'wait': 3.0
        },
        ErrorType.BROWSER_HANG: {
            'retry': 1,
            'action': 'restart_browser',
            'log_level': 'CRITICAL',
            'wait': 5.0
        },
        ErrorType.LLM_TIMEOUT: {
            'retry': 3,
            'action': 'exponential_backoff',
            'log_level': 'WARNING',
            'wait': 2.0
        },
        ErrorType.FILE_ACCESS_ERROR: {
            'retry': 2,
            'action': 'check_permissions',
            'log_level': 'ERROR',
            'wait': 1.0
        },
        ErrorType.NETWORK_ERROR: {
            'retry': 3,
            'action': 'check_connection',
            'log_level': 'ERROR',
            'wait': 5.0
        }
    }
    
    def __init__(self, config: dict, log_callback: Callable):
        self.config = config
        self.log = log_callback
        self.error_count = {}
        self.recovery_actions = {
            'retry_with_alt_image': self._retry_with_alt_image,
            'wait_and_retry': self._wait_and_retry,
            'restart_browser': self._restart_browser,
            'exponential_backoff': self._exponential_backoff,
            'check_permissions': self._check_permissions,
            'check_connection': self._check_connection
        }
        
    def handle_error(
        self,
        error_type: ErrorType,
        context: Dict,
        callback: Optional[Callable] = None
    ) -> bool:
        """
        에러 처리 메인 메서드
        
        Args:
            error_type: 에러 타입
            context: 에러 컨텍스트 정보
            callback: 복구 후 재시도할 함수
            
        Returns:
            bool: 복구 성공 여부
        """
        strategy = self.ERROR_STRATEGIES.get(error_type)
        
        if not strategy:
            self.log("ERROR", f"알 수 없는 에러 타입: {error_type}")
            return False
            
        # 에러 카운트 증가
        error_key = f"{error_type}_{context.get('product_id', 'unknown')}"
        self.error_count[error_key] = self.error_count.get(error_key, 0) + 1
        
        # 로깅
        self.log(
            strategy['log_level'],
            f"에러 발생: {error_type.value} (시도 {self.error_count[error_key]}/{strategy['retry']})"
        )
        
        # 재시도 한계 확인
        if self.error_count[error_key] > strategy['retry']:
            self.log("ERROR", f"재시도 한계 초과: {error_type.value}")
            return False
            
        # 복구 액션 실행
        action_name = strategy['action']
        recovery_action = self.recovery_actions.get(action_name)
        
        if recovery_action:
            success = recovery_action(context, strategy)
            
            # 콜백 실행 (재시도)
            if success and callback:
                return callback()
                
            return success
            
        return False
        
    def _retry_with_alt_image(self, context: Dict, strategy: Dict) -> bool:
        """대체 이미지로 재시도"""
        self.log("INFO", "대체 이미지로 재시도 중...")
        time.sleep(strategy['wait'])
        
        # 대체 이미지 경로 확인
        alt_image = context.get('alternative_image')
        if alt_image:
            context['primary_image'] = alt_image
            return True
            
        return False
        
    def _wait_and_retry(self, context: Dict, strategy: Dict) -> bool:
        """대기 후 재시도"""
        wait_time = strategy['wait']
        self.log("INFO", f"{wait_time}초 대기 후 재시도...")
        time.sleep(wait_time)
        return True
        
    def _restart_browser(self, context: Dict, strategy: Dict) -> bool:
        """브라우저 재시작"""
        self.log("WARNING", "브라우저 재시작 중...")
        
        try:
            # 브라우저 종료
            if self.config['web_automation']['browser'] == 'chrome':
                subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe'], check=False)
                time.sleep(2)
                
                # 브라우저 재시작
                subprocess.Popen(['start', 'chrome'], shell=True)
                time.sleep(5)
                
            return True
            
        except Exception as e:
            self.log("ERROR", f"브라우저 재시작 실패: {str(e)}")
            return False
            
    def _exponential_backoff(self, context: Dict, strategy: Dict) -> bool:
        """지수 백오프 재시도"""
        attempt = context.get('attempt', 1)
        wait_time = strategy['wait'] * (2 ** (attempt - 1))
        
        self.log("INFO", f"지수 백오프: {wait_time}초 대기")
        time.sleep(wait_time)
        
        context['attempt'] = attempt + 1
        return True
        
    def _check_permissions(self, context: Dict, strategy: Dict) -> bool:
        """파일 권한 확인"""
        file_path = context.get('file_path')
        
        if file_path:
            from pathlib import Path
            path = Path(file_path)
            
            if not path.parent.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                self.log("INFO", f"폴더 생성: {path.parent}")
                return True
                
        return False
        
    def _check_connection(self, context: Dict, strategy: Dict) -> bool:
        """네트워크 연결 확인"""
        import requests
        
        try:
            response = requests.get('https://www.google.com', timeout=5)
            if response.status_code == 200:
                self.log("INFO", "네트워크 연결 정상")
                return True
                
        except Exception as e:
            self.log("ERROR", f"네트워크 연결 실패: {str(e)}")
            
        time.sleep(strategy['wait'])
        return False