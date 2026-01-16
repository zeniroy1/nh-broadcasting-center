export const facilities = [
    // 본관 (Main Building)
    {
        id: 'main-auditorium',
        name: '대강당',
        building: 'main',
        category: 'meeting',
        capacity: '',
        location: '본관 로비층',
        description: '정례 행사, 외부 대규모 행사, 세미나, 교육 등을 진행할 수 있는 다목적 공간입니다.',
        equipment: ['대형 LED 전광판', '영상,음향 시스템', '조명', '연단'],
        image: '/assets/auditorium_real_1.jpg',
        subItems: [
            {
                id: 'auditorium-photos',
                title: '대강당 사진',
                type: 'image-gallery',
                images: [
                    { url: '/assets/auditorium_real_1.jpg', caption: '중앙회 행사 예시1' },
                    { url: '/assets/auditorium_real_2.jpg', caption: '중앙회 행사 예시2' },
                    { url: '/assets/auditorium_real_3.jpg', caption: '외부 행사 예시1' },
                    { url: '/assets/auditorium_real_4.jpg', caption: '외부 행사 예시2' },
                    { url: '/assets/auditorium_real_5.jpg', caption: '외부 행사 예시3' },
                    { url: '/assets/auditorium_real_6.jpg', caption: '외부 행사 예시4' },
                    { url: '/assets/auditorium_real_7.jpg', caption: '외부 행사 예시5' },
                    { url: '/assets/auditorium_real_8.jpg', caption: '외부 행사 예시6' },
                    { url: '/assets/auditorium_real_9.jpg', caption: '행사 조감도 예시1' },
                    { url: '/assets/auditorium_real_10.jpg', caption: '행사 조감도 예시2' },
                ],
                description: '대강당의 다양한 모습을 확인하실 수 있습니다.'
            },
            {
                id: 'stage-layout',
                title: '무대관련도면',
                type: 'image-gallery',
                images: [
                    {
                        url: 'https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?auto=format&fit=crop&q=80&w=1000',
                        caption: '무대 평면도 (Stage Plan)'
                    },
                    {
                        url: 'https://images.unsplash.com/photo-1503387762-592deb58ef4e?auto=format&fit=crop&q=80&w=1000',
                        caption: '무대 단면도 (Stage Section)'
                    }
                ],
                description: '대강당 무대 크기 및 조명/음향 배치가 포함된 상세 도면입니다. 클릭하여 이미지를 확대할 수 있습니다.'
            },
            {
                id: 'broadcast-status',
                title: '방송지원 현황',
                type: 'rich-content',
                sections: [
                    {
                        title: '마이크 지원',
                        color: '#4A89DC', // Blue
                        items: [
                            '유선 마이크 8개 (사회석2, 의장석2, 무대연단2, 발언석2)',
                            '무선 마이크 8개 (핸드 8개, 이어 마이크 1개와 교체가능)'
                        ]
                    },
                    {
                        title: '영상/음향 지원',
                        color: '#967ADC', // Purple
                        items: [
                            '녹음, 녹화 (USB 4G 이상 지참, 1층 방송운영단 수령)',
                            '전광판 (사용자 노트북, HDMI 연결)',
                            '전자현수막 지원',
                            '국민의례, 농협의 노래 지원',
                            '식전, 시상식 음악 (시나리오 별도 표기 요청)'
                        ]
                    },
                    {
                        title: '운영 지원',
                        color: '#37BC9B', // Teal
                        items: [
                            'DID 식순 안내 (총무팀 : 6010)',
                            '냉난방 지원 (관제실 : 5119)'
                        ]
                    },
                    {
                        title: '주요 시설 규격',
                        color: '#E9573F', // Orange
                        items: [
                            '무대 사이즈 : 가로 17m x 세로 8.5m',
                            '전광판 사이즈 : 560인치 (가로 13m x 세로 6m)',
                            '전자현수막 사이즈 : 가로 13m x 세로 0.7m',
                            '대강당 면적 : 무대 포함 300평'
                        ]
                    }
                ]
            },
            {
                id: 'stage-facilities',
                title: '무대시설 현황',
                type: 'rich-content',
                sections: [
                    {
                        title: '전자 현수막 사이즈',
                        color: '#5D9CEC', // Blue
                        items: ['1300cm(가로) x 71cm(높이) x 30cm(폭)']
                    },
                    {
                        title: 'LED 전광판 화면 크기',
                        color: '#FC6E51', // Red/Orange
                        items: [
                            '가로 13M x 세로(높이) 6M (563.77 인치)',
                            '최적 해상도 : 4368*1848 (26:11)',
                            '1920*812'
                        ]
                    },
                    {
                        title: '무대 크기 (넓이)',
                        color: '#AC92EC', // Purple
                        items: [
                            '1800cm(가로) x 870cm(세로) → 전체 크기',
                            '1665cm(가로) x 860cm(세로) → 실사용 면적',
                            '대강당 홀 전체 크기 : 연단 무대 위 포함 약 300평'
                        ]
                    },
                    {
                        title: '무대 높이',
                        color: '#48CFAD', // Teal
                        items: [
                            '홀 바닥 ~ 무대 높이 : 100cm(높이)',
                            '이동식 계단 : 총 4개'
                        ]
                    },
                    {
                        title: '바텐 길이, 높이',
                        subTitle: '(총 전체 길이 : 1650cm)',
                        color: '#FFCE54', // Yellow
                        items: [
                            '무대 바닥 ~ 천정 그릴 끝까지 : 665cm (높이)',
                            '무대 바닥 ~ 최대로 내린 상태 : 150cm (높이)',
                            '무대 바닥 ~ 머리막 커튼까지 : 570cm (높이)'
                        ]
                    },
                    {
                        title: '무대 바텐 허용 무게',
                        color: '#A0D468', // Green
                        items: [
                            '최대하중 지탱 무게 : 1.5t (최대 허용치)',
                            '안전 허용 무게 : 1t'
                        ]
                    },
                    {
                        title: '스피커 출력',
                        color: '#ED5565', // Red
                        items: [
                            '라인어레이(16대) : 3.9KW*16 = 62.4KW',
                            '서브우퍼(4대) : 3.2KW*4 = 12.8KW',
                            '센터 스피커(1대) : 0.55KW*1 = 0.55KW',
                            '후면 보조 스피커(2대) : 0.3KW*2 = 0.6KW',
                            '총 대강당 출력(최대출력 기준) : 96.35KW'
                        ]
                    },
                    {
                        title: '외부팀 전기 사용',
                        color: '#4FC1E9', // Light Blue
                        items: [
                            '대강당 후면 75A 1기',
                            '대강당 후면 200A 1기'
                        ]
                    }
                ]
            },
            {
                id: 'banner-file',
                title: '전자현수막파일', // Updated title
                type: 'file-download',
                description: '대강당 전자현수막 게시 요청 시 아래 가이드를 준수하여 파일을 제작해 주시기 바랍니다.',
                guideLines: [
                    '아래 첨부된 샘플 파일을 다운받아 내용 수정 후 보내주시면 됩니다.',
                    '첨부 파일을 그림판, 포토샵, PhotoScape X, GIMP, 포토피아 등 이미지 편집 프로그램으로 현수막 안의 내용만 수정하시면 됩니다.',
                    '사이즈나 비율을 조정하면 전광판에 안 맞거나 저화질로 흐리게 표출될 수 있으니 유의하세요.',
                    '외부 대행사 통해 이미지 제작 하시더라도 아래 샘플 파일로 작업해서 보내주십시오.',
                    '고해상도로 작업해도 시스템에서 지원이 안됩니다.',
                    '회의에 사용하실 완성본은 방송운영단 메일(nh5994@naver.com)로 보내시고 메일 제목과 파일명은 날짜 행사명으로 해주세요. 예) 2022-00-00 정기이사회',
                    'PPT로 편집 시 화질 저하 및 사이즈 변경되니 꼭 이미지 편집 프로그램(그림판, 포토샵 등)을 사용하여 편집 하세요.'
                ],
                downloads: [
                    {
                        name: '전자현수막 샘플 1',
                        fileUrl: '/assets/banner_sample_1.png',
                        previewUrl: '/assets/banner_sample_1.png',
                        size: '1300 x 71 px'
                    },
                    {
                        name: '전자현수막 샘플 2',
                        fileUrl: '/assets/banner_sample_2.png',
                        previewUrl: '/assets/banner_sample_2.png',
                        size: '1300 x 71 px'
                    }
                ]
            }
        ],
        images: [
            '/assets/auditorium_real_1.jpg',
            '/assets/auditorium_real_2.jpg',
            '/assets/auditorium_real_3.jpg',
            '/assets/auditorium_real_4.jpg',
            '/assets/auditorium_real_5.jpg',
            '/assets/auditorium_real_6.jpg',
            '/assets/auditorium_real_7.jpg',
            '/assets/auditorium_real_8.jpg',
            '/assets/auditorium_real_9.jpg',
            '/assets/auditorium_real_10.jpg'
        ]
    },
    {
        id: 'main-medium-conf',
        name: '중회의실',
        building: 'main',
        category: 'meeting',
        capacity: '',
        location: '본관 2층',
        description: '부서 간 회의나 중규모 미팅에 적합한 공간입니다.',
        equipment: ['LED 전광판', '회의용 MIC', '영상,음향 시스템'],
        image: '/assets/medium_conf_real_1.jpg',
        images: [
            '/assets/medium_conf_real_1.jpg',
            '/assets/medium_conf_real_2.jpg',
            '/assets/medium_conf_real_3.jpg',
            '/assets/medium_conf_real_4.jpg',
            '/assets/medium_conf_real_5.jpg',
            '/assets/medium_conf_real_6.jpg',
            '/assets/medium_conf_real_7.jpg',
            '/assets/medium_conf_real_8.jpg'
        ],
        subItems: [
            {
                id: 'medium-conf-photos',
                title: '중회의실 사진',
                type: 'image-gallery',
                images: [
                    { url: '/assets/medium_conf_real_1.jpg', caption: '중회의실 전경 1' },
                    { url: '/assets/medium_conf_real_2.jpg', caption: '중회의실 전경 2' },
                    { url: '/assets/medium_conf_real_3.jpg', caption: '중회의실 전경 3' },
                    { url: '/assets/medium_conf_real_4.jpg', caption: '중회의실 전경 4' },
                    { url: '/assets/medium_conf_real_5.jpg', caption: '중회의실 전경 5' },
                    { url: '/assets/medium_conf_real_6.jpg', caption: '중회의실 전경 6' },
                    { url: '/assets/medium_conf_real_7.jpg', caption: '장비 소개 1' },
                    { url: '/assets/medium_conf_real_8.jpg', caption: '장비 소개 2' }
                ],
                description: '중회의실의 다양한 모습과 장비 현황을 확인하실 수 있습니다.'
            },
            {
                id: 'medium-broadcast-status',
                title: '방송지원 현황',
                type: 'rich-content',
                sections: [
                    {
                        title: '방송지원',
                        color: '#4A89DC', // Blue
                        items: [
                            '유선 마이크 4개 (사회석 2개, 의장석 2개)',
                            '무선 마이크 4개',
                            '이어 마이크 1개 (이어 마이크 사용시 무선핸드는 3개만 사용가능)',
                            '회의용 마이크 25개 (목책상만 설치 가능)',
                            'LED 전광판 (사용자 노트북, HDMI 연결)',
                            '녹음, 녹화 (USB 4G 이상 지참, 1층 방송운영단 수령)',
                            '국민의례, 농협의 노래 (음원 지원)',
                            '식전, 시상식 음악 (시나리오 별도 표기 요청)',
                            'DID 전자 식순 (총무팀 : 6010)',
                            '냉난방 지원 (관제실 : 5119)'
                        ]
                    },
                    {
                        title: '시설 현황',
                        color: '#37BC9B', // Teal
                        items: [
                            'LED 전광판 사이즈 : 160인치 (가로 3.6m x 세로 2m)',
                            '현수막 사이즈 : 가로 6m x 세로 0.7m',
                            '무대 사이즈 : 가로 13m x 세로 3m',
                            '최대 수용 인원 : 200명',
                            '개별 냉난방 가능',
                            '인터넷 (내부망 / 외부망)'
                        ]
                    }
                ]
            }
        ]
    },
    {
        id: 'main-video-conf',
        name: '화상회의실',
        building: 'main',
        category: 'meeting',
        capacity: '',
        location: '본관 2층',
        description: '원격지와의 원활한 커뮤니케이션을 위한 화상 회의 시스템을 갖추고 있습니다.',
        equipment: ['화상회의 pc', 'LED전광판', '영상,음향 시스템'],
        image: '/assets/video_conf_real_1.jpg',
        images: [
            '/assets/video_conf_real_1.jpg',
            '/assets/video_conf_real_2.jpg',
            '/assets/video_conf_real_3.jpg'
        ],
        subItems: [
            {
                id: 'video-conf-photos',
                title: '화상회의실 사진',
                type: 'image-gallery',
                images: [
                    { url: '/assets/video_conf_real_1.jpg', caption: '화상회의실 전경 1' },
                    { url: '/assets/video_conf_real_2.jpg', caption: '화상회의실 전경 2' },
                    { url: '/assets/video_conf_real_3.jpg', caption: '화상회의실 전경 3' }
                ],
                description: '최첨단 화상 회의 시스템이 갖춰진 회의실의 모습입니다.'
            },
            {
                id: 'video-conf-broadcast-status',
                title: '방송지원현황',
                type: 'rich-content',
                sections: [
                    {
                        title: '방송지원',
                        subTitle: '※ 전자 명패, 전자교탁, 화상회의 사용시 총무팀(6010)으로 사전 문의 바랍니다.',
                        color: '#4A89DC', // Blue
                        items: [
                            '유선 마이크 1개 (사회석)',
                            '무선 마이크 2개',
                            '회의용 마이크 31개 (고정형, 이동 불가)',
                            '녹음, 녹화 (4G 이상 USB 지참, 1층 방송실에서 수령 가능)',
                            'LED 전광판 (사용자 노트북 HDMI 연결)',
                            '국민의례, 식전음악',
                            '전자명패',
                            '전자교탁',
                            '신 화상회의 시스템 (zoom회의 불가)'
                        ]
                    },
                    {
                        title: '시설 현황',
                        color: '#37BC9B', // Teal
                        items: [
                            'LED 전광판 사이즈 : 160인치 (가로 3.6m x 세로 2m)',
                            '현수막 사이즈 : 560cm x 55cm',
                            '최대 수용 인원 : 61명 (고정)',
                            '개별 냉난방 가능',
                            '인터넷 (내부망 / 외부망)'
                        ]
                    },
                    {
                        title: '주의사항',
                        subTitle: '※ 의장석 이동, 자리 배치 변경을 원하실 경우 중회의실을 사용하셔야 합니다.',
                        color: '#E9573F', // Red
                        items: [
                            '화상회의실 신 화상회의 시스템은 회의실 사용자 측이 직접 운영합니다.',
                            '화상회의 진행 중 시스템 내 장애 발생, 참석자 접속 설정 방법 미숙으로 인한 소리울림 또는 잡음이 일어나지 않도록 미리 테스트하셔야 합니다.',
                            '신 화상회의 시스템 사용 시 최소 3일전 사전 리허설 시간을 예약하여 충분히 확인 후 진행 하셔야 합니다.',
                            'ZOOM 화상회의는 현재 지원이 되지 않습니다.',
                            '화상회의실 회의용 장비는 모두 고정형으로써 이동 배치가 불가합니다.'
                        ]
                    }
                ]
            }
        ]
    },
    {
        id: 'main-small-conf',
        name: '소회의실',
        building: 'main',
        category: 'meeting',
        capacity: '',
        location: '본관 1층',
        description: '팀 단위 회의나 소규모 미팅을 위한 공간입니다.',
        equipment: ['전자칠판', '음향시스템'],
        image: 'https://images.unsplash.com/photo-1577412647305-991150c7d163?auto=format&fit=crop&q=80&w=1000',
        images: [
            'https://images.unsplash.com/photo-1577412647305-991150c7d163?auto=format&fit=crop&q=80&w=1000',
            'https://images.unsplash.com/photo-1517048676732-d65bc937f952?auto=format&fit=crop&q=80&w=1000',
            'https://images.unsplash.com/photo-1431540015161-0bf868a2d407?auto=format&fit=crop&q=80&w=1000',
            'https://images.unsplash.com/photo-1570126618953-d437145e8c25?auto=format&fit=crop&q=80&w=1000'
        ]
    },
    {
        id: 'main-strategy-room',
        name: '경영전략회의실',
        building: 'main',
        category: 'meeting',
        capacity: '',
        location: '본관 4층',
        description: '중요한 의사결정과 전략 수립을 위한 VIP 회의 공간입니다.',
        equipment: ['', '', ''],
        image: 'https://images.unsplash.com/photo-1556761175-5973dc0f32e7?auto=format&fit=crop&q=80&w=1000',
        images: [
            'https://images.unsplash.com/photo-1556761175-5973dc0f32e7?auto=format&fit=crop&q=80&w=1000',
            'https://images.unsplash.com/photo-1497366811353-6870744d04b2?auto=format&fit=crop&q=80&w=1000',
            'https://images.unsplash.com/photo-1497215728101-856f4ea42174?auto=format&fit=crop&q=80&w=1000',
            'https://images.unsplash.com/photo-1664575602276-acd073f104c1?auto=format&fit=crop&q=80&w=1000'
        ]
    },
    {
        id: 'main-cafeteria',
        name: '신토불이, 두레식당',
        building: 'main',
        category: 'amenities',
        capacity: '',
        location: '본관 지하2층',
        description: '임직원의 건강과 맛을 책임지는 구내 식당입니다.',
        equipment: ['자율 배식대', ''],
        image: 'https://images.unsplash.com/photo-1590846406792-0adc7f938f1d?auto=format&fit=crop&q=80&w=1000',
        images: [
            'https://images.unsplash.com/photo-1590846406792-0adc7f938f1d?auto=format&fit=crop&q=80&w=1000',
            'https://images.unsplash.com/photo-1554118811-1e0d58224f24?auto=format&fit=crop&q=80&w=1000',
            'https://images.unsplash.com/photo-1588612148175-71cb1bf584e0?auto=format&fit=crop&q=80&w=1000',
            'https://images.unsplash.com/photo-1565895405139-e188df996e0c?auto=format&fit=crop&q=80&w=1000'
        ]
    },
    {
        id: 'main-lobby',
        name: '로비전광판',
        building: 'main',
        category: 'amenities',
        capacity: '-',
        location: '본관 로비층',
        description: '주요 일정과 환영 메시지를 송출하는 대형 디스플레이입니다.',
        equipment: ['LED 디스플레이', '운영 PC'],
        image: 'https://images.unsplash.com/photo-1542744173-8e7e53415bb0?auto=format&fit=crop&q=80&w=1000',
        images: [
            'https://images.unsplash.com/photo-1542744173-8e7e53415bb0?auto=format&fit=crop&q=80&w=1000',
            'https://images.unsplash.com/photo-1497215728101-856f4ea42174?auto=format&fit=crop&q=80&w=1000',
            'https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?auto=format&fit=crop&q=80&w=1000',
            'https://images.unsplash.com/photo-1497366754035-f200968a6e72?auto=format&fit=crop&q=80&w=1000'
        ]
    },
    {
        id: 'main-situation-room',
        name: '상황실',
        building: 'main',
        category: 'operations',
        capacity: '',
        location: '본관 5층',
        description: '방송 송출 현황과 시스템 상태를 24시간 모니터링하는 통제 센터입니다.',
        equipment: ['', '', ''],
        image: 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&q=80&w=1000',
        images: [
            'https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&q=80&w=1000',
            'https://images.unsplash.com/photo-1542744094-3a31f272c490?auto=format&fit=crop&q=80&w=1000',
            'https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&q=80&w=1000',
            'https://images.unsplash.com/photo-1504384308090-c54be3855091?auto=format&fit=crop&q=80&w=1000'
        ]
    },
    {
        id: 'main-mobile-equip',
        name: '이동형 음향장비',
        building: 'main',
        category: 'operations',
        capacity: '-',
        location: '본관 장비실',
        description: '행사 지원을 위한 이동식 방송/음향 장비입니다.',
        equipment: ['이동식 앰프', '무선 마이크 세트', ''],
        image: 'https://images.unsplash.com/photo-1520529986492-5b32630e363a?auto=format&fit=crop&q=80&w=1000',
        images: [
            'https://images.unsplash.com/photo-1520529986492-5b32630e363a?auto=format&fit=crop&q=80&w=1000',
            'https://images.unsplash.com/photo-1516280440614-6697288d5d38?auto=format&fit=crop&q=80&w=1000',
            'https://images.unsplash.com/photo-1598488035139-bdbb2231ce04?auto=format&fit=crop&q=80&w=1000',
            'https://images.unsplash.com/photo-1563811771046-ba984ff30900?auto=format&fit=crop&q=80&w=1000'
        ]
    },

    // 신관 (New Building)
    {
        id: 'new-grand-conf',
        name: '대회의실',
        building: 'new',
        category: 'meeting',
        capacity: '',
        location: '신관 3층',
        description: '넓은 공간과 최신 설비를 갖춘 대형 회의실입니다.',
        equipment: ['대형 LED 전광판', '화상회의 시스템', '영상,음향 시스템'],
        image: 'https://images.unsplash.com/photo-1505373877841-8d25f7d46678?auto=format&fit=crop&q=80&w=1000',
        images: [
            'https://images.unsplash.com/photo-1505373877841-8d25f7d46678?auto=format&fit=crop&q=80&w=1000',
            'https://images.unsplash.com/photo-1517502884422-41e157d258b7?auto=format&fit=crop&q=80&w=1000',
            'https://images.unsplash.com/photo-1560179707-f14e90ef3623?auto=format&fit=crop&q=80&w=1000',
            'https://images.unsplash.com/photo-1497366811353-6870744d04b2?auto=format&fit=crop&q=80&w=1000'
        ]
    },
    {
        id: 'new-medium-conf',
        name: '중회의실',
        building: 'new',
        category: 'meeting',
        capacity: '25명',
        location: '신관 3층',
        description: '쾌적한 환경의 중규모 회의 공간입니다.',
        equipment: ['LED 전광판', '영상,음향 시스템', '무선 마이크', '화이트보드'],
        image: 'https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&q=80&w=1000',
        images: [
            'https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&q=80&w=1000',
            'https://images.unsplash.com/photo-1542744173-8e7e53415bb0?auto=format&fit=crop&q=80&w=1000',
            'https://images.unsplash.com/photo-1504384764586-bb4cdc1707b0?auto=format&fit=crop&q=80&w=1000',
            'https://images.unsplash.com/photo-1497366754035-f200968a6e72?auto=format&fit=crop&q=80&w=1000'
        ],
        subItems: [
            {
                id: 'new-medium-conf-photos',
                title: '중회의실 사진',
                type: 'image-gallery',
                images: [
                    { url: 'https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&q=80&w=1000', caption: '중회의실 전경' },
                    { url: 'https://images.unsplash.com/photo-1542744173-8e7e53415bb0?auto=format&fit=crop&q=80&w=1000', caption: '회의 테이블' }
                ],
                description: '신관 중회의실의 깔끔하고 모던한 인테리어를 확인하세요.'
            },
            {
                id: 'new-medium-broadcast-status',
                title: '방송지원 현황',
                type: 'rich-content',
                sections: [
                    {
                        title: '방송지원',
                        color: '#4A89DC',
                        items: [
                            '유선 마이크 2개',
                            '무선 마이크 2개',
                            '이동형 TV (HDMI 연결)',
                            '녹음 지원 불가 (개별 녹음기 지참 필요)'
                        ]
                    },
                    {
                        title: '시설 현황',
                        color: '#37BC9B',
                        items: [
                            '최대 수용 인원 : 25명',
                            '화이트보드 비치',
                            '개별 냉난방 가능',
                            'WIFI 사용 가능'
                        ]
                    }
                ]
            }
        ]
    },
    {
        id: 'new-small-conf',
        name: '1, 2, 3소회의실',
        building: 'new',
        category: 'meeting',
        capacity: '',
        location: '신관 3층',
        description: '집중도 높은 소규모 미팅을 위한 독립된 공간들입니다.',
        equipment: ['전광판', '영상,음향 시스템'],
        image: 'https://images.unsplash.com/photo-1587825140708-dfaf72ae4b04?auto=format&fit=crop&q=80&w=1000',
        images: [
            'https://images.unsplash.com/photo-1587825140708-dfaf72ae4b04?auto=format&fit=crop&q=80&w=1000',
            'https://images.unsplash.com/photo-1517502884422-41e157d258b7?auto=format&fit=crop&q=80&w=1000',
            'https://images.unsplash.com/photo-1497366811353-6870744d04b2?auto=format&fit=crop&q=80&w=1000',
            'https://images.unsplash.com/photo-1664575602276-acd073f104c1?auto=format&fit=crop&q=80&w=1000'
        ]
    },
    {
        id: 'new-cafeteria',
        name: '채움마루, 행복마루 식당',
        building: 'new',
        category: 'amenities',
        capacity: '',
        location: '신관 21층',
        description: '다양한 메뉴와 편안한 휴식을 제공하는 신관 식당입니다.',
        equipment: ['카페', '휴게 라운지'],
        image: 'https://images.unsplash.com/photo-1554118811-1e0d58224f24?auto=format&fit=crop&q=80&w=1000',
        images: [
            'https://images.unsplash.com/photo-1554118811-1e0d58224f24?auto=format&fit=crop&q=80&w=1000',
            'https://images.unsplash.com/photo-1529333166437-7750a6dd5a70?auto=format&fit=crop&q=80&w=1000',
            'https://images.unsplash.com/photo-1590846406792-0adc7f938f1d?auto=format&fit=crop&q=80&w=1000',
            'https://images.unsplash.com/photo-1424847651672-bf202175b04a?auto=format&fit=crop&q=80&w=1000'
        ]
    },
    {
        id: 'new-strategy-room',
        name: '경영전략회의실',
        building: 'new',
        category: 'meeting',
        capacity: '',
        location: '신관 4층',
        description: '핵심 의사결정을 위한 프리미엄 회의실입니다.',
        equipment: ['화상회의', ''],
        image: 'https://images.unsplash.com/photo-1431540015161-0bf868a2d407?auto=format&fit=crop&q=80&w=1000',
        images: [
            'https://images.unsplash.com/photo-1431540015161-0bf868a2d407?auto=format&fit=crop&q=80&w=1000',
            'https://images.unsplash.com/photo-1497366811353-6870744d04b2?auto=format&fit=crop&q=80&w=1000',
            'https://images.unsplash.com/photo-1664575602276-acd073f104c1?auto=format&fit=crop&q=80&w=1000',
            'https://images.unsplash.com/photo-1577412647305-991150c7d163?auto=format&fit=crop&q=80&w=1000'
        ]
    }
];

export const buildings = [
    { id: 'main', name: '본관', description: 'Main Building' },
    { id: 'new', name: '신관', description: 'New Building' }
];
