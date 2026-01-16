module.exports = [
"[project]/src/data/facilities.js [app-ssr] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "buildings",
    ()=>buildings,
    "facilities",
    ()=>facilities
]);
const facilities = [
    // 본관 (Main Building)
    {
        id: 'main-auditorium',
        name: '대강당',
        building: 'main',
        category: 'meeting',
        capacity: '200명',
        location: '본관 2층',
        description: '대규모 행사, 세미나, 교육 등을 진행할 수 있는 다목적 공간입니다.',
        equipment: [
            '대형 스크린',
            '음향 시스템',
            '조명 설비',
            '연단'
        ],
        image: '/assets/auditorium/a/hq-1.png',
        subItems: [
            {
                id: 'auditorium-hq-photos',
                title: '중앙본부 행사',
                type: 'image-gallery',
                images: [
                    {
                        url: '/assets/auditorium/a/hq-1.png',
                        caption: '중앙본부 행사 예시 1'
                    },
                    {
                        url: '/assets/auditorium/a/hq-2.jpg',
                        caption: '중앙본부 행사 예시 2'
                    },
                    {
                        url: '/assets/auditorium/a/hq-3.jpg',
                        caption: '중앙본부 행사 예시 3'
                    }
                ],
                description: '중앙본부 행사 진행 모습입니다.'
            },
            {
                id: 'auditorium-ext-photos',
                title: '외부 행사',
                type: 'image-gallery',
                images: [
                    {
                        url: '/assets/auditorium/b/ext-1.jpg',
                        caption: '외부 행사 예시 1'
                    },
                    {
                        url: '/assets/auditorium/b/ext-2.jpg',
                        caption: '외부 행사 예시 2'
                    },
                    {
                        url: '/assets/auditorium/b/ext-3.jpg',
                        caption: '외부 행사 예시 3'
                    },
                    {
                        url: '/assets/auditorium/b/ext-4.jpg',
                        caption: '외부 행사 예시 4'
                    },
                    {
                        url: '/assets/auditorium/b/ext-5.jpg',
                        caption: '외부 행사 예시 5'
                    }
                ],
                description: '외부 대관 행사 진행 모습입니다.'
            },
            {
                id: 'auditorium-diagrams',
                title: '행사 조감도',
                type: 'image-gallery',
                images: [
                    {
                        url: '/assets/auditorium/c/diagram-1.jpg',
                        caption: '행사 조감도 1'
                    },
                    {
                        url: '/assets/auditorium/c/diagram-2.jpg',
                        caption: '행사 조감도 2'
                    }
                ],
                description: '행사 배치 조감도 예시입니다.'
            },
            {
                id: 'broadcast-status',
                title: '방송지원 현황',
                type: 'rich-content',
                sections: [
                    {
                        title: '마이크 지원',
                        color: '#4A89DC',
                        items: [
                            '유선 마이크 8개 (사회석2, 의장석2, 무대연단2, 발언석2)',
                            '무선 마이크 8개 (핸드 8개, 이어 마이크 1개와 교체가능)'
                        ]
                    },
                    {
                        title: '영상/음향 지원',
                        color: '#967ADC',
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
                        color: '#37BC9B',
                        items: [
                            'DID 식순 안내 (총무팀 : 6010)',
                            '냉난방 지원 (관제실 : 5119)'
                        ]
                    },
                    {
                        title: '주요 시설 규격',
                        color: '#E9573F',
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
                        color: '#5D9CEC',
                        items: [
                            '1300cm(가로) x 71cm(높이) x 30cm(폭)'
                        ]
                    },
                    {
                        title: 'LED 전광판 화면 크기',
                        color: '#FC6E51',
                        items: [
                            '가로 13M x 세로(높이) 6M (563.77 인치)',
                            '최적 해상도 : 4368*1848 (26:11)',
                            '1920*812'
                        ]
                    },
                    {
                        title: '무대 크기 (넓이)',
                        color: '#AC92EC',
                        items: [
                            '1800cm(가로) x 870cm(세로) → 전체 크기',
                            '1665cm(가로) x 860cm(세로) → 실사용 면적',
                            '대강당 홀 전체 크기 : 연단 무대 위 포함 약 300평'
                        ]
                    },
                    {
                        title: '무대 높이',
                        color: '#48CFAD',
                        items: [
                            '홀 바닥 ~ 무대 높이 : 100cm(높이)',
                            '이동식 계단 : 총 4개'
                        ]
                    },
                    {
                        title: '바텐 길이, 높이',
                        subTitle: '(총 전체 길이 : 1650cm)',
                        color: '#FFCE54',
                        items: [
                            '무대 바닥 ~ 천정 그릴 끝까지 : 665cm (높이)',
                            '무대 바닥 ~ 최대로 내린 상태 : 150cm (높이)',
                            '무대 바닥 ~ 머리막 커튼까지 : 570cm (높이)'
                        ]
                    },
                    {
                        title: '무대 바텐 허용 무게',
                        color: '#A0D468',
                        items: [
                            '최대하중 지탱 무게 : 1.5t (최대 허용치)',
                            '안전 허용 무게 : 1t'
                        ]
                    },
                    {
                        title: '스피커 출력',
                        color: '#ED5565',
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
                        color: '#4FC1E9',
                        items: [
                            '대강당 후면 75A 1기',
                            '대강당 후면 200A 1기'
                        ]
                    }
                ]
            },
            {
                id: 'banner-file',
                title: '전자현수막파일',
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
            '/assets/auditorium/a/hq-1.png',
            '/assets/auditorium/a/hq-2.jpg',
            '/assets/auditorium/b/ext-1.jpg',
            '/assets/auditorium/c/diagram-1.jpg'
        ]
    },
    {
        id: 'main-medium-conf',
        name: '중회의실',
        building: 'main',
        category: 'meeting',
        capacity: '30명',
        location: '본관 3층',
        description: '부서 간 회의나 중규모 미팅에 적합한 공간입니다.',
        equipment: [
            '빔프로젝터',
            '화이트보드',
            '무선 마이크'
        ],
        image: '/assets/medium_conf/a/view-1.jpg',
        images: [
            '/assets/medium_conf/a/view-1.jpg',
            '/assets/medium_conf/a/view-2.jpg',
            '/assets/medium_conf/a/view-3.jpg',
            '/assets/medium_conf/a/view-4.jpg'
        ],
        subItems: [
            {
                id: 'medium-conf-photos',
                title: '중회의실 전경',
                type: 'image-gallery',
                images: [
                    {
                        url: '/assets/medium_conf/a/view-1.jpg',
                        caption: '중회의실 전경 1'
                    },
                    {
                        url: '/assets/medium_conf/a/view-2.jpg',
                        caption: '중회의실 전경 2'
                    },
                    {
                        url: '/assets/medium_conf/a/view-3.jpg',
                        caption: '중회의실 전경 3'
                    },
                    {
                        url: '/assets/medium_conf/a/view-4.jpg',
                        caption: '중회의실 전경 4'
                    },
                    {
                        url: '/assets/medium_conf/a/view-5.jpg',
                        caption: '중회의실 전경 5'
                    },
                    {
                        url: '/assets/medium_conf/a/view-6.jpg',
                        caption: '중회의실 전경 6'
                    }
                ],
                description: '중회의실의 다양한 모습입니다.'
            },
            {
                id: 'medium-conf-equipment',
                title: '장비 현황',
                type: 'image-gallery',
                images: [
                    {
                        url: '/assets/medium_conf/b/equip-1.jpg',
                        caption: '장비 및 시설 1'
                    },
                    {
                        url: '/assets/medium_conf/b/equip-2.jpg',
                        caption: '장비 및 시설 2'
                    }
                ],
                description: '중회의실 장비 및 세부 시설입니다.'
            },
            {
                id: 'medium-broadcast-status',
                title: '방송지원 현황',
                type: 'rich-content',
                sections: [
                    {
                        title: '방송지원',
                        color: '#4A89DC',
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
                        color: '#37BC9B',
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
        capacity: '15명',
        location: '본관 3층',
        description: '원격지와의 원활한 소통을 위한 최첨단 화상 회의 시스템을 갖추고 있습니다.',
        equipment: [
            '화상회의 코덱',
            '듀얼 모니터',
            '방음 시설'
        ],
        image: '/assets/video_conf/view-1.jpg',
        images: [
            '/assets/video_conf/view-1.jpg',
            '/assets/video_conf/view-2.jpg',
            '/assets/video_conf/view-3.jpg'
        ],
        subItems: [
            {
                id: 'video-conf-photos',
                title: '화상회의실 사진',
                type: 'image-gallery',
                images: [
                    {
                        url: '/assets/video_conf/view-1.jpg',
                        caption: '화상회의실 전경 1'
                    },
                    {
                        url: '/assets/video_conf/view-2.jpg',
                        caption: '화상회의실 전경 2'
                    },
                    {
                        url: '/assets/video_conf/view-3.jpg',
                        caption: '화상회의실 전경 3'
                    }
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
                        color: '#4A89DC',
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
                        color: '#37BC9B',
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
                        color: '#E9573F',
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
        capacity: '8명',
        location: '본관 3층',
        description: '팀 단위 회의나 소규모 미팅을 위한 아늑한 공간입니다.',
        equipment: [
            '모니터',
            '화이트보드'
        ],
        image: 'https://images.unsplash.com/photo-1577412647305-991150c7d163?auto=format&fit=crop&q=80&w=1000'
    },
    {
        id: 'main-strategy-room',
        name: '경영전략회의실',
        building: 'main',
        category: 'meeting',
        capacity: '20명',
        location: '본관 4층',
        description: '중요한 의사결정과 전략 수립을 위한 VIP 회의 공간입니다.',
        equipment: [
            '스마트 보드',
            '고급 가구',
            '보안 시스템'
        ],
        image: 'https://images.unsplash.com/photo-1556761175-5973dc0f32e7?auto=format&fit=crop&q=80&w=1000'
    },
    {
        id: 'main-cafeteria',
        name: '신토불이, 두레식당',
        building: 'main',
        category: 'amenities',
        capacity: '150명',
        location: '본관 1층',
        description: '임직원의 건강과 맛을 책임지는 구내 식당입니다.',
        equipment: [
            '자율 배식대',
            '카페테리아'
        ],
        image: 'https://images.unsplash.com/photo-1590846406792-0adc7f938f1d?auto=format&fit=crop&q=80&w=1000'
    },
    {
        id: 'main-lobby',
        name: '로비전광판',
        building: 'main',
        category: 'amenities',
        capacity: '-',
        location: '본관 1층 로비',
        description: '주요 공지사항과 환영 메시지를 송출하는 대형 디스플레이입니다.',
        equipment: [
            'LED 디스플레이',
            '운영 PC'
        ],
        image: 'https://images.unsplash.com/photo-1542744173-8e7e53415bb0?auto=format&fit=crop&q=80&w=1000'
    },
    {
        id: 'main-situation-room',
        name: '상황실',
        building: 'main',
        category: 'operations',
        capacity: '10명',
        location: '본관 5층',
        description: '방송 송출 현황과 시스템 상태를 24시간 모니터링하는 통제 센터입니다.',
        equipment: [
            '멀티비전',
            '모니터링 시스템',
            '비상 통신망'
        ],
        image: 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&q=80&w=1000'
    },
    {
        id: 'main-mobile-equip',
        name: '이동장비',
        building: 'main',
        category: 'operations',
        capacity: '-',
        location: '본관 장비실',
        description: '행사 지원을 위한 이동식 방송/음향 장비입니다.',
        equipment: [
            '이동식 앰프',
            '무선 마이크 세트',
            '카메라'
        ],
        image: 'https://images.unsplash.com/photo-1520529986492-5b32630e363a?auto=format&fit=crop&q=80&w=1000'
    },
    // 신관 (New Building)
    {
        id: 'new-grand-conf',
        name: '대회의실',
        building: 'new',
        category: 'meeting',
        capacity: '100명',
        location: '신관 2층',
        description: '넓은 공간과 최신 설비를 갖춘 대형 회의실입니다.',
        equipment: [
            '대형 프로젝터',
            '화상회의 시스템',
            '강의용 음향'
        ],
        image: 'https://images.unsplash.com/photo-1505373877841-8d25f7d46678?auto=format&fit=crop&q=80&w=1000'
    },
    {
        id: 'new-medium-conf',
        name: '중회의실',
        building: 'new',
        category: 'meeting',
        capacity: '40명',
        location: '신관 3층',
        description: '쾌적한 환경의 중규모 회의 공간입니다.',
        equipment: [
            '스마트 TV',
            '글라스 보드'
        ],
        image: 'https://images.unsplash.com/photo-1517502884422-41e157d258b7?auto=format&fit=crop&q=80&w=1000'
    },
    {
        id: 'new-small-conf',
        name: '1, 2, 3소회의실',
        building: 'new',
        category: 'meeting',
        capacity: '10명',
        location: '신관 3층',
        description: '집중도 높은 소규모 미팅을 위한 독립된 공간들입니다.',
        equipment: [
            '모니터',
            '화이트보드'
        ],
        image: 'https://images.unsplash.com/photo-1587825140708-dfaf72ae4b04?auto=format&fit=crop&q=80&w=1000'
    },
    {
        id: 'new-cafeteria',
        name: '채움마루, 행복마루 식당',
        building: 'new',
        category: 'amenities',
        capacity: '200명',
        location: '신관 1층',
        description: '다양한 메뉴와 편안한 휴식을 제공하는 신관 식당입니다.',
        equipment: [
            '카페',
            '휴게 라운지'
        ],
        image: 'https://images.unsplash.com/photo-1554118811-1e0d58224f24?auto=format&fit=crop&q=80&w=1000'
    },
    {
        id: 'new-strategy-room',
        name: '경영전략회의실',
        building: 'new',
        category: 'meeting',
        capacity: '25명',
        location: '신관 4층',
        description: '신관의 핵심 의사결정을 위한 프리미엄 회의실입니다.',
        equipment: [
            '최고급 화상회의',
            '보안 시스템'
        ],
        image: 'https://images.unsplash.com/photo-1431540015161-0bf868a2d407?auto=format&fit=crop&q=80&w=1000'
    }
];
const buildings = [
    {
        id: 'main',
        name: '본관',
        description: 'Main Building'
    },
    {
        id: 'new',
        name: '신관',
        description: 'New Building'
    }
];
}),
"[project]/components/facilities/FacilityCard.js [app-ssr] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "FacilityCard",
    ()=>FacilityCard
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/server/route-modules/app-page/vendored/ssr/react-jsx-dev-runtime.js [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Card$2f$Card$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@mantine/core/esm/components/Card/Card.mjs [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Image$2f$Image$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@mantine/core/esm/components/Image/Image.mjs [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Text$2f$Text$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@mantine/core/esm/components/Text/Text.mjs [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Badge$2f$Badge$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@mantine/core/esm/components/Badge/Badge.mjs [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Group$2f$Group$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@mantine/core/esm/components/Group/Group.mjs [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Button$2f$Button$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@mantine/core/esm/components/Button/Button.mjs [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$framer$2d$motion$2f$dist$2f$es$2f$render$2f$components$2f$motion$2f$proxy$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/framer-motion/dist/es/render/components/motion/proxy.mjs [app-ssr] (ecmascript)");
'use client';
;
;
;
function FacilityCard({ facility, onClick }) {
    const Component = __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$framer$2d$motion$2f$dist$2f$es$2f$render$2f$components$2f$motion$2f$proxy$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["motion"].create(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Card$2f$Card$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Card"]); // Create motion component from Mantine Card
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(Component, {
        shadow: "sm",
        padding: "lg",
        radius: "lg",
        withBorder: true,
        layout: true,
        initial: {
            opacity: 0,
            scale: 0.9
        },
        animate: {
            opacity: 1,
            scale: 1
        },
        exit: {
            opacity: 0,
            scale: 0.9
        },
        whileHover: {
            y: -5,
            boxShadow: '0 10px 20px rgba(0,0,0,0.1)'
        },
        onClick: ()=>onClick(facility),
        style: {
            cursor: 'pointer',
            height: '100%'
        },
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Card$2f$Card$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Card"].Section, {
                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Image$2f$Image$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Image"], {
                    src: facility.image,
                    height: 200,
                    alt: facility.name,
                    fallbackSrc: "https://placehold.co/600x400?text=No+Image"
                }, void 0, false, {
                    fileName: "[project]/components/facilities/FacilityCard.js",
                    lineNumber: 24,
                    columnNumber: 17
                }, this)
            }, void 0, false, {
                fileName: "[project]/components/facilities/FacilityCard.js",
                lineNumber: 23,
                columnNumber: 13
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Group$2f$Group$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Group"], {
                justify: "space-between",
                mt: "md",
                mb: "xs",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Text$2f$Text$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Text"], {
                        fw: 700,
                        size: "lg",
                        children: facility.name
                    }, void 0, false, {
                        fileName: "[project]/components/facilities/FacilityCard.js",
                        lineNumber: 33,
                        columnNumber: 17
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Badge$2f$Badge$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Badge"], {
                        color: "gray",
                        variant: "light",
                        children: facility.location
                    }, void 0, false, {
                        fileName: "[project]/components/facilities/FacilityCard.js",
                        lineNumber: 34,
                        columnNumber: 17
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/components/facilities/FacilityCard.js",
                lineNumber: 32,
                columnNumber: 13
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Text$2f$Text$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Text"], {
                size: "sm",
                c: "dimmed",
                lineClamp: 2,
                style: {
                    minHeight: '40px'
                },
                children: facility.description
            }, void 0, false, {
                fileName: "[project]/components/facilities/FacilityCard.js",
                lineNumber: 37,
                columnNumber: 13
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Group$2f$Group$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Group"], {
                gap: "xs",
                mt: "md",
                children: facility.equipment?.slice(0, 3).map((item, index)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Badge$2f$Badge$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Badge"], {
                        size: "sm",
                        variant: "outline",
                        color: "gray",
                        children: item
                    }, index, false, {
                        fileName: "[project]/components/facilities/FacilityCard.js",
                        lineNumber: 43,
                        columnNumber: 21
                    }, this))
            }, void 0, false, {
                fileName: "[project]/components/facilities/FacilityCard.js",
                lineNumber: 41,
                columnNumber: 13
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Button$2f$Button$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Button"], {
                variant: "light",
                color: "blue",
                fullWidth: true,
                mt: "md",
                radius: "md",
                children: "상세보기"
            }, void 0, false, {
                fileName: "[project]/components/facilities/FacilityCard.js",
                lineNumber: 49,
                columnNumber: 13
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/components/facilities/FacilityCard.js",
        lineNumber: 10,
        columnNumber: 9
    }, this);
}
}),
"[project]/components/facilities/FacilityModal.js [app-ssr] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "FacilityModal",
    ()=>FacilityModal
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/server/route-modules/app-page/vendored/ssr/react-jsx-dev-runtime.js [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/server/route-modules/app-page/vendored/ssr/react.js [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Modal$2f$Modal$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@mantine/core/esm/components/Modal/Modal.mjs [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Text$2f$Text$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@mantine/core/esm/components/Text/Text.mjs [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Image$2f$Image$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@mantine/core/esm/components/Image/Image.mjs [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Group$2f$Group$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@mantine/core/esm/components/Group/Group.mjs [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Badge$2f$Badge$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@mantine/core/esm/components/Badge/Badge.mjs [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Tabs$2f$Tabs$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@mantine/core/esm/components/Tabs/Tabs.mjs [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$ThemeIcon$2f$ThemeIcon$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@mantine/core/esm/components/ThemeIcon/ThemeIcon.mjs [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$List$2f$List$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@mantine/core/esm/components/List/List.mjs [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$ScrollArea$2f$ScrollArea$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@mantine/core/esm/components/ScrollArea/ScrollArea.mjs [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$tabler$2f$icons$2d$react$2f$dist$2f$esm$2f$icons$2f$IconPhoto$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__$3c$export__default__as__IconPhoto$3e$__ = __turbopack_context__.i("[project]/node_modules/@tabler/icons-react/dist/esm/icons/IconPhoto.mjs [app-ssr] (ecmascript) <export default as IconPhoto>");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$tabler$2f$icons$2d$react$2f$dist$2f$esm$2f$icons$2f$IconListDetails$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__$3c$export__default__as__IconListDetails$3e$__ = __turbopack_context__.i("[project]/node_modules/@tabler/icons-react/dist/esm/icons/IconListDetails.mjs [app-ssr] (ecmascript) <export default as IconListDetails>");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$tabler$2f$icons$2d$react$2f$dist$2f$esm$2f$icons$2f$IconTools$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__$3c$export__default__as__IconTools$3e$__ = __turbopack_context__.i("[project]/node_modules/@tabler/icons-react/dist/esm/icons/IconTools.mjs [app-ssr] (ecmascript) <export default as IconTools>");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$carousel$2f$esm$2f$Carousel$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@mantine/carousel/esm/Carousel.mjs [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$embla$2d$carousel$2d$autoplay$2f$esm$2f$embla$2d$carousel$2d$autoplay$2e$esm$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/embla-carousel-autoplay/esm/embla-carousel-autoplay.esm.js [app-ssr] (ecmascript)");
'use client';
;
;
;
;
;
;
;
function FacilityModal({ facility, onClose }) {
    const [previewImage, setPreviewImage] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useState"])(null);
    const autoplay = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useRef"])((0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$embla$2d$carousel$2d$autoplay$2f$esm$2f$embla$2d$carousel$2d$autoplay$2e$esm$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["default"])({
        delay: 3000
    }));
    if (!facility) return null;
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Fragment"], {
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Modal$2f$Modal$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Modal"], {
                opened: !!facility && !previewImage,
                onClose: onClose,
                title: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Text$2f$Text$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Text"], {
                    fw: 700,
                    size: "xl",
                    children: facility.name
                }, void 0, false, {
                    fileName: "[project]/components/facilities/FacilityModal.js",
                    lineNumber: 21,
                    columnNumber: 24
                }, void 0),
                size: "xl",
                radius: "lg",
                padding: "xl",
                centered: true,
                scrollAreaComponent: __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$ScrollArea$2f$ScrollArea$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["ScrollArea"].Autosize,
                zIndex: 200,
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Image$2f$Image$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Image"], {
                        src: facility.image,
                        height: 300,
                        radius: "md",
                        alt: facility.name,
                        fallbackSrc: "https://placehold.co/600x400?text=No+Image",
                        mb: "xl",
                        style: {
                            cursor: 'pointer'
                        },
                        onClick: ()=>setPreviewImage(facility.image)
                    }, void 0, false, {
                        fileName: "[project]/components/facilities/FacilityModal.js",
                        lineNumber: 29,
                        columnNumber: 17
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Tabs$2f$Tabs$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Tabs"], {
                        defaultValue: "info",
                        color: "blue",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Tabs$2f$Tabs$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Tabs"].List, {
                                mb: "md",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Tabs$2f$Tabs$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Tabs"].Tab, {
                                        value: "info",
                                        leftSection: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$tabler$2f$icons$2d$react$2f$dist$2f$esm$2f$icons$2f$IconListDetails$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__$3c$export__default__as__IconListDetails$3e$__["IconListDetails"], {
                                            size: 16
                                        }, void 0, false, {
                                            fileName: "[project]/components/facilities/FacilityModal.js",
                                            lineNumber: 42,
                                            columnNumber: 61
                                        }, void 0),
                                        children: "기본 정보"
                                    }, void 0, false, {
                                        fileName: "[project]/components/facilities/FacilityModal.js",
                                        lineNumber: 42,
                                        columnNumber: 25
                                    }, this),
                                    facility.subItems && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Fragment"], {
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Tabs$2f$Tabs$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Tabs"].Tab, {
                                                value: "gallery",
                                                leftSection: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$tabler$2f$icons$2d$react$2f$dist$2f$esm$2f$icons$2f$IconPhoto$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__$3c$export__default__as__IconPhoto$3e$__["IconPhoto"], {
                                                    size: 16
                                                }, void 0, false, {
                                                    fileName: "[project]/components/facilities/FacilityModal.js",
                                                    lineNumber: 47,
                                                    columnNumber: 72
                                                }, void 0),
                                                children: "갤러리"
                                            }, void 0, false, {
                                                fileName: "[project]/components/facilities/FacilityModal.js",
                                                lineNumber: 47,
                                                columnNumber: 33
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Tabs$2f$Tabs$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Tabs"].Tab, {
                                                value: "specs",
                                                leftSection: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$tabler$2f$icons$2d$react$2f$dist$2f$esm$2f$icons$2f$IconTools$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__$3c$export__default__as__IconTools$3e$__["IconTools"], {
                                                    size: 16
                                                }, void 0, false, {
                                                    fileName: "[project]/components/facilities/FacilityModal.js",
                                                    lineNumber: 50,
                                                    columnNumber: 70
                                                }, void 0),
                                                children: "상세 제원"
                                            }, void 0, false, {
                                                fileName: "[project]/components/facilities/FacilityModal.js",
                                                lineNumber: 50,
                                                columnNumber: 33
                                            }, this)
                                        ]
                                    }, void 0, true)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/components/facilities/FacilityModal.js",
                                lineNumber: 41,
                                columnNumber: 21
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Tabs$2f$Tabs$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Tabs"].Panel, {
                                value: "info",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Text$2f$Text$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Text"], {
                                        size: "lg",
                                        mb: "md",
                                        children: facility.description
                                    }, void 0, false, {
                                        fileName: "[project]/components/facilities/FacilityModal.js",
                                        lineNumber: 58,
                                        columnNumber: 25
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Group$2f$Group$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Group"], {
                                        gap: "xl",
                                        mb: "xl",
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                children: [
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Text$2f$Text$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Text"], {
                                                        size: "sm",
                                                        c: "dimmed",
                                                        children: "위치"
                                                    }, void 0, false, {
                                                        fileName: "[project]/components/facilities/FacilityModal.js",
                                                        lineNumber: 62,
                                                        columnNumber: 33
                                                    }, this),
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Text$2f$Text$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Text"], {
                                                        fw: 500,
                                                        children: facility.location
                                                    }, void 0, false, {
                                                        fileName: "[project]/components/facilities/FacilityModal.js",
                                                        lineNumber: 63,
                                                        columnNumber: 33
                                                    }, this)
                                                ]
                                            }, void 0, true, {
                                                fileName: "[project]/components/facilities/FacilityModal.js",
                                                lineNumber: 61,
                                                columnNumber: 29
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                children: [
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Text$2f$Text$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Text"], {
                                                        size: "sm",
                                                        c: "dimmed",
                                                        children: "수용 인원"
                                                    }, void 0, false, {
                                                        fileName: "[project]/components/facilities/FacilityModal.js",
                                                        lineNumber: 66,
                                                        columnNumber: 33
                                                    }, this),
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Text$2f$Text$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Text"], {
                                                        fw: 500,
                                                        children: facility.capacity
                                                    }, void 0, false, {
                                                        fileName: "[project]/components/facilities/FacilityModal.js",
                                                        lineNumber: 67,
                                                        columnNumber: 33
                                                    }, this)
                                                ]
                                            }, void 0, true, {
                                                fileName: "[project]/components/facilities/FacilityModal.js",
                                                lineNumber: 65,
                                                columnNumber: 29
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/components/facilities/FacilityModal.js",
                                        lineNumber: 60,
                                        columnNumber: 25
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Text$2f$Text$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Text"], {
                                        fw: 600,
                                        mb: "sm",
                                        children: "보유 장비"
                                    }, void 0, false, {
                                        fileName: "[project]/components/facilities/FacilityModal.js",
                                        lineNumber: 71,
                                        columnNumber: 25
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Group$2f$Group$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Group"], {
                                        gap: "xs",
                                        children: facility.equipment?.map((item, index)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Badge$2f$Badge$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Badge"], {
                                                size: "lg",
                                                variant: "dot",
                                                children: item
                                            }, index, false, {
                                                fileName: "[project]/components/facilities/FacilityModal.js",
                                                lineNumber: 74,
                                                columnNumber: 33
                                            }, this))
                                    }, void 0, false, {
                                        fileName: "[project]/components/facilities/FacilityModal.js",
                                        lineNumber: 72,
                                        columnNumber: 25
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/components/facilities/FacilityModal.js",
                                lineNumber: 57,
                                columnNumber: 21
                            }, this),
                            facility.subItems && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Fragment"], {
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Tabs$2f$Tabs$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Tabs"].Panel, {
                                        value: "gallery",
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$carousel$2f$esm$2f$Carousel$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Carousel"], {
                                                withIndicators: true,
                                                height: 400,
                                                slideSize: "100%",
                                                slideGap: "md",
                                                loop: true,
                                                align: "start",
                                                plugins: [
                                                    autoplay.current
                                                ],
                                                onMouseEnter: autoplay.current.stop,
                                                onMouseLeave: autoplay.current.reset,
                                                children: facility.subItems.find((item)=>item.type === 'image-gallery')?.images.map((img, idx)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$carousel$2f$esm$2f$Carousel$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Carousel"].Slide, {
                                                        children: [
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Image$2f$Image$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Image"], {
                                                                src: img.url,
                                                                radius: "md",
                                                                h: 400,
                                                                fit: "cover",
                                                                style: {
                                                                    cursor: 'pointer'
                                                                },
                                                                onClick: ()=>setPreviewImage(img.url)
                                                            }, void 0, false, {
                                                                fileName: "[project]/components/facilities/FacilityModal.js",
                                                                lineNumber: 95,
                                                                columnNumber: 45
                                                            }, this),
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Text$2f$Text$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Text"], {
                                                                size: "sm",
                                                                ta: "center",
                                                                mt: 4,
                                                                c: "dimmed",
                                                                children: img.caption
                                                            }, void 0, false, {
                                                                fileName: "[project]/components/facilities/FacilityModal.js",
                                                                lineNumber: 103,
                                                                columnNumber: 45
                                                            }, this)
                                                        ]
                                                    }, idx, true, {
                                                        fileName: "[project]/components/facilities/FacilityModal.js",
                                                        lineNumber: 94,
                                                        columnNumber: 41
                                                    }, this))
                                            }, void 0, false, {
                                                fileName: "[project]/components/facilities/FacilityModal.js",
                                                lineNumber: 82,
                                                columnNumber: 33
                                            }, this),
                                            !facility.subItems.find((item)=>item.type === 'image-gallery') && facility.images && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$carousel$2f$esm$2f$Carousel$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Carousel"], {
                                                withIndicators: true,
                                                height: 400,
                                                slideSize: "100%",
                                                slideGap: "md",
                                                loop: true,
                                                align: "start",
                                                plugins: [
                                                    autoplay.current
                                                ],
                                                onMouseEnter: autoplay.current.stop,
                                                onMouseLeave: autoplay.current.reset,
                                                children: facility.images.map((img, idx)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$carousel$2f$esm$2f$Carousel$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Carousel"].Slide, {
                                                        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Image$2f$Image$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Image"], {
                                                            src: img,
                                                            radius: "md",
                                                            h: 400,
                                                            fit: "cover",
                                                            style: {
                                                                cursor: 'pointer'
                                                            },
                                                            onClick: ()=>setPreviewImage(img)
                                                        }, void 0, false, {
                                                            fileName: "[project]/components/facilities/FacilityModal.js",
                                                            lineNumber: 122,
                                                            columnNumber: 49
                                                        }, this)
                                                    }, idx, false, {
                                                        fileName: "[project]/components/facilities/FacilityModal.js",
                                                        lineNumber: 121,
                                                        columnNumber: 45
                                                    }, this))
                                            }, void 0, false, {
                                                fileName: "[project]/components/facilities/FacilityModal.js",
                                                lineNumber: 109,
                                                columnNumber: 37
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/components/facilities/FacilityModal.js",
                                        lineNumber: 81,
                                        columnNumber: 29
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Tabs$2f$Tabs$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Tabs"].Panel, {
                                        value: "specs",
                                        children: facility.subItems.filter((item)=>item.type === 'rich-content').map((section, idx)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                style: {
                                                    marginBottom: '2rem'
                                                },
                                                children: [
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Text$2f$Text$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Text"], {
                                                        fw: 700,
                                                        size: "lg",
                                                        mb: "md",
                                                        children: section.title
                                                    }, void 0, false, {
                                                        fileName: "[project]/components/facilities/FacilityModal.js",
                                                        lineNumber: 139,
                                                        columnNumber: 41
                                                    }, this),
                                                    section.sections.map((subSec, sIdx)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                            style: {
                                                                marginBottom: '1rem',
                                                                padding: '1rem',
                                                                backgroundColor: 'var(--mantine-color-gray-1)',
                                                                borderRadius: '8px',
                                                                borderLeft: `4px solid ${subSec.color || '#ccc'}`
                                                            },
                                                            children: [
                                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Text$2f$Text$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Text"], {
                                                                    fw: 600,
                                                                    mb: "xs",
                                                                    c: subSec.color,
                                                                    children: subSec.title
                                                                }, void 0, false, {
                                                                    fileName: "[project]/components/facilities/FacilityModal.js",
                                                                    lineNumber: 142,
                                                                    columnNumber: 49
                                                                }, this),
                                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$List$2f$List$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["List"], {
                                                                    size: "sm",
                                                                    spacing: "xs",
                                                                    icon: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$ThemeIcon$2f$ThemeIcon$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["ThemeIcon"], {
                                                                        color: subSec.color,
                                                                        size: 6,
                                                                        radius: "xl",
                                                                        variant: "filled"
                                                                    }, void 0, false, {
                                                                        fileName: "[project]/components/facilities/FacilityModal.js",
                                                                        lineNumber: 143,
                                                                        columnNumber: 84
                                                                    }, void 0),
                                                                    children: subSec.items.map((item, iIdx)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$List$2f$List$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["List"].Item, {
                                                                            children: item
                                                                        }, iIdx, false, {
                                                                            fileName: "[project]/components/facilities/FacilityModal.js",
                                                                            lineNumber: 145,
                                                                            columnNumber: 57
                                                                        }, this))
                                                                }, void 0, false, {
                                                                    fileName: "[project]/components/facilities/FacilityModal.js",
                                                                    lineNumber: 143,
                                                                    columnNumber: 49
                                                                }, this)
                                                            ]
                                                        }, sIdx, true, {
                                                            fileName: "[project]/components/facilities/FacilityModal.js",
                                                            lineNumber: 141,
                                                            columnNumber: 45
                                                        }, this))
                                                ]
                                            }, idx, true, {
                                                fileName: "[project]/components/facilities/FacilityModal.js",
                                                lineNumber: 138,
                                                columnNumber: 37
                                            }, this))
                                    }, void 0, false, {
                                        fileName: "[project]/components/facilities/FacilityModal.js",
                                        lineNumber: 136,
                                        columnNumber: 29
                                    }, this)
                                ]
                            }, void 0, true)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/facilities/FacilityModal.js",
                        lineNumber: 40,
                        columnNumber: 17
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/components/facilities/FacilityModal.js",
                lineNumber: 18,
                columnNumber: 13
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Modal$2f$Modal$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Modal"], {
                opened: !!previewImage,
                onClose: ()=>setPreviewImage(null),
                size: "100%",
                fullScreen: true,
                zIndex: 300,
                withCloseButton: true,
                styles: {
                    body: {
                        padding: 0,
                        background: 'rgba(0,0,0,0.9)',
                        height: '100vh',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                    },
                    header: {
                        position: 'absolute',
                        top: 0,
                        right: 0,
                        zIndex: 301,
                        background: 'transparent'
                    }
                },
                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Image$2f$Image$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Image"], {
                    src: previewImage,
                    fit: "contain",
                    h: "100%",
                    w: "100%",
                    onClick: ()=>setPreviewImage(null)
                }, void 0, false, {
                    fileName: "[project]/components/facilities/FacilityModal.js",
                    lineNumber: 171,
                    columnNumber: 17
                }, this)
            }, void 0, false, {
                fileName: "[project]/components/facilities/FacilityModal.js",
                lineNumber: 159,
                columnNumber: 13
            }, this)
        ]
    }, void 0, true);
}
}),
"[project]/app/facilities/page.js [app-ssr] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "default",
    ()=>Facilities
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/server/route-modules/app-page/vendored/ssr/react-jsx-dev-runtime.js [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/server/route-modules/app-page/vendored/ssr/react.js [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Container$2f$Container$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@mantine/core/esm/components/Container/Container.mjs [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Title$2f$Title$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@mantine/core/esm/components/Title/Title.mjs [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Text$2f$Text$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@mantine/core/esm/components/Text/Text.mjs [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$SimpleGrid$2f$SimpleGrid$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@mantine/core/esm/components/SimpleGrid/SimpleGrid.mjs [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Group$2f$Group$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@mantine/core/esm/components/Group/Group.mjs [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$TextInput$2f$TextInput$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@mantine/core/esm/components/TextInput/TextInput.mjs [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$SegmentedControl$2f$SegmentedControl$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@mantine/core/esm/components/SegmentedControl/SegmentedControl.mjs [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$core$2f$Box$2f$Box$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@mantine/core/esm/core/Box/Box.mjs [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$LoadingOverlay$2f$LoadingOverlay$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@mantine/core/esm/components/LoadingOverlay/LoadingOverlay.mjs [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Image$2f$Image$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@mantine/core/esm/components/Image/Image.mjs [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$search$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__$3c$export__default__as__Search$3e$__ = __turbopack_context__.i("[project]/node_modules/lucide-react/dist/esm/icons/search.js [app-ssr] (ecmascript) <export default as Search>");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$building$2d$2$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__$3c$export__default__as__Building2$3e$__ = __turbopack_context__.i("[project]/node_modules/lucide-react/dist/esm/icons/building-2.js [app-ssr] (ecmascript) <export default as Building2>");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$framer$2d$motion$2f$dist$2f$es$2f$render$2f$components$2f$motion$2f$proxy$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/framer-motion/dist/es/render/components/motion/proxy.mjs [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$framer$2d$motion$2f$dist$2f$es$2f$components$2f$AnimatePresence$2f$index$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/framer-motion/dist/es/components/AnimatePresence/index.mjs [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$navigation$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/navigation.js [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$carousel$2f$esm$2f$Carousel$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@mantine/carousel/esm/Carousel.mjs [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$embla$2d$carousel$2d$autoplay$2f$esm$2f$embla$2d$carousel$2d$autoplay$2e$esm$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/embla-carousel-autoplay/esm/embla-carousel-autoplay.esm.js [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$data$2f$facilities$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/data/facilities.js [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$facilities$2f$FacilityCard$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/components/facilities/FacilityCard.js [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$facilities$2f$FacilityModal$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/components/facilities/FacilityModal.js [app-ssr] (ecmascript)");
'use client';
;
;
;
;
;
;
;
;
;
;
;
;
function FacilitiesContent() {
    const [activeBuilding, setActiveBuilding] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useState"])('main');
    const [selectedFacility, setSelectedFacility] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useState"])(null);
    const [searchTerm, setSearchTerm] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useState"])('');
    const searchParams = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$navigation$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useSearchParams"])();
    const autoplay = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useRef"])((0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$embla$2d$carousel$2d$autoplay$2f$esm$2f$embla$2d$carousel$2d$autoplay$2e$esm$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["default"])({
        delay: 3000
    }));
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useEffect"])(()=>{
        const type = searchParams.get('type');
        if (type) {
            const facility = __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$data$2f$facilities$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["facilities"].find((f)=>f.id === type);
            if (facility) {
                setActiveBuilding(facility.building);
                setSelectedFacility(facility);
            }
        }
    }, [
        searchParams
    ]);
    const filteredFacilities = __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$data$2f$facilities$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["facilities"].filter((f)=>{
        const matchesBuilding = f.building === activeBuilding;
        const matchesSearch = f.name.includes(searchTerm) || f.description.includes(searchTerm) || f.equipment?.some((e)=>e.includes(searchTerm));
        return matchesBuilding && matchesSearch;
    });
    const featuredImages = [
        {
            src: '/assets/auditorium_real_1.jpg',
            title: '대강당',
            desc: '최첨단 음향 시설과 대형 스크린'
        },
        {
            src: '/assets/medium_conf_real_1.jpg',
            title: '중회의실',
            desc: '효율적인 비즈니스 미팅'
        },
        {
            src: '/assets/video_conf_real_1.jpg',
            title: '화상회의실',
            desc: '글로벌 소통의 중심'
        }
    ];
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Container$2f$Container$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Container"], {
        size: "xl",
        py: "xl",
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$core$2f$Box$2f$Box$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Box"], {
                mb: 50,
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$carousel$2f$esm$2f$Carousel$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Carousel"], {
                        withIndicators: true,
                        height: 400,
                        slideSize: "100%",
                        slideGap: "md",
                        loop: true,
                        align: "start",
                        plugins: [
                            autoplay.current
                        ],
                        onMouseEnter: autoplay.current.stop,
                        onMouseLeave: autoplay.current.reset,
                        style: {
                            borderRadius: '16px',
                            overflow: 'hidden',
                            boxShadow: '0 8px 30px rgba(0,0,0,0.1)'
                        },
                        mb: "xl",
                        children: featuredImages.map((item, index)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$carousel$2f$esm$2f$Carousel$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Carousel"].Slide, {
                                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$core$2f$Box$2f$Box$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Box"], {
                                    pos: "relative",
                                    h: "100%",
                                    children: [
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Image$2f$Image$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Image"], {
                                            src: item.src,
                                            h: "100%",
                                            fit: "cover"
                                        }, void 0, false, {
                                            fileName: "[project]/app/facilities/page.js",
                                            lineNumber: 67,
                                            columnNumber: 33
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$core$2f$Box$2f$Box$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Box"], {
                                            style: {
                                                position: 'absolute',
                                                bottom: 0,
                                                left: 0,
                                                right: 0,
                                                padding: '40px',
                                                background: 'linear-gradient(to top, rgba(0,0,0,0.8), transparent)',
                                                color: 'white'
                                            },
                                            children: [
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Title$2f$Title$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Title"], {
                                                    order: 2,
                                                    mb: "xs",
                                                    children: item.title
                                                }, void 0, false, {
                                                    fileName: "[project]/app/facilities/page.js",
                                                    lineNumber: 77,
                                                    columnNumber: 37
                                                }, this),
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Text$2f$Text$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Text"], {
                                                    size: "lg",
                                                    c: "gray.2",
                                                    children: item.desc
                                                }, void 0, false, {
                                                    fileName: "[project]/app/facilities/page.js",
                                                    lineNumber: 78,
                                                    columnNumber: 37
                                                }, this)
                                            ]
                                        }, void 0, true, {
                                            fileName: "[project]/app/facilities/page.js",
                                            lineNumber: 68,
                                            columnNumber: 33
                                        }, this)
                                    ]
                                }, void 0, true, {
                                    fileName: "[project]/app/facilities/page.js",
                                    lineNumber: 66,
                                    columnNumber: 29
                                }, this)
                            }, index, false, {
                                fileName: "[project]/app/facilities/page.js",
                                lineNumber: 65,
                                columnNumber: 25
                            }, this))
                    }, void 0, false, {
                        fileName: "[project]/app/facilities/page.js",
                        lineNumber: 51,
                        columnNumber: 17
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$core$2f$Box$2f$Box$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Box"], {
                        style: {
                            textAlign: 'center'
                        },
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$framer$2d$motion$2f$dist$2f$es$2f$render$2f$components$2f$motion$2f$proxy$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["motion"].div, {
                                initial: {
                                    opacity: 0,
                                    y: -20
                                },
                                animate: {
                                    opacity: 1,
                                    y: 0
                                },
                                transition: {
                                    duration: 0.5
                                },
                                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$building$2d$2$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__$3c$export__default__as__Building2$3e$__["Building2"], {
                                    size: 48,
                                    color: "#007AFF",
                                    style: {
                                        marginBottom: '1rem'
                                    }
                                }, void 0, false, {
                                    fileName: "[project]/app/facilities/page.js",
                                    lineNumber: 91,
                                    columnNumber: 25
                                }, this)
                            }, void 0, false, {
                                fileName: "[project]/app/facilities/page.js",
                                lineNumber: 86,
                                columnNumber: 21
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Title$2f$Title$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Title"], {
                                order: 1,
                                mb: "sm",
                                style: {
                                    fontFamily: 'var(--font-sf)',
                                    fontWeight: 800,
                                    fontSize: '3rem'
                                },
                                children: "시설 안내"
                            }, void 0, false, {
                                fileName: "[project]/app/facilities/page.js",
                                lineNumber: 93,
                                columnNumber: 21
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Text$2f$Text$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Text"], {
                                c: "dimmed",
                                size: "lg",
                                maw: 600,
                                mx: "auto",
                                children: "NH 방송운영단의 최첨단 시설을 본관과 신관으로 나누어 소개합니다."
                            }, void 0, false, {
                                fileName: "[project]/app/facilities/page.js",
                                lineNumber: 96,
                                columnNumber: 21
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/app/facilities/page.js",
                        lineNumber: 85,
                        columnNumber: 17
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/app/facilities/page.js",
                lineNumber: 50,
                columnNumber: 13
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Group$2f$Group$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Group"], {
                justify: "center",
                mb: "xl",
                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$SegmentedControl$2f$SegmentedControl$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["SegmentedControl"], {
                    value: activeBuilding,
                    onChange: setActiveBuilding,
                    data: __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$data$2f$facilities$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["buildings"].map((b)=>({
                            label: b.name,
                            value: b.id
                        })),
                    size: "lg",
                    radius: "xl",
                    color: "blue",
                    bg: "gray.1"
                }, void 0, false, {
                    fileName: "[project]/app/facilities/page.js",
                    lineNumber: 104,
                    columnNumber: 17
                }, this)
            }, void 0, false, {
                fileName: "[project]/app/facilities/page.js",
                lineNumber: 103,
                columnNumber: 13
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Group$2f$Group$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Group"], {
                justify: "flex-end",
                mb: "xl",
                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$TextInput$2f$TextInput$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["TextInput"], {
                    placeholder: "장소 검색...",
                    leftSection: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$search$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__$3c$export__default__as__Search$3e$__["Search"], {
                        size: 16
                    }, void 0, false, {
                        fileName: "[project]/app/facilities/page.js",
                        lineNumber: 118,
                        columnNumber: 34
                    }, void 0),
                    radius: "md",
                    value: searchTerm,
                    onChange: (e)=>setSearchTerm(e.currentTarget.value),
                    style: {
                        width: '300px'
                    }
                }, void 0, false, {
                    fileName: "[project]/app/facilities/page.js",
                    lineNumber: 116,
                    columnNumber: 17
                }, this)
            }, void 0, false, {
                fileName: "[project]/app/facilities/page.js",
                lineNumber: 115,
                columnNumber: 13
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$framer$2d$motion$2f$dist$2f$es$2f$render$2f$components$2f$motion$2f$proxy$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["motion"].div, {
                layout: true,
                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$SimpleGrid$2f$SimpleGrid$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["SimpleGrid"], {
                    cols: {
                        base: 1,
                        sm: 2,
                        lg: 3
                    },
                    spacing: "xl",
                    children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$framer$2d$motion$2f$dist$2f$es$2f$components$2f$AnimatePresence$2f$index$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["AnimatePresence"], {
                        mode: "popLayout",
                        children: filteredFacilities.map((facility)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$components$2f$facilities$2f$FacilityCard$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["FacilityCard"], {
                                facility: facility,
                                onClick: setSelectedFacility
                            }, facility.id, false, {
                                fileName: "[project]/app/facilities/page.js",
                                lineNumber: 131,
                                columnNumber: 29
                            }, this))
                    }, void 0, false, {
                        fileName: "[project]/app/facilities/page.js",
                        lineNumber: 129,
                        columnNumber: 21
                    }, this)
                }, void 0, false, {
                    fileName: "[project]/app/facilities/page.js",
                    lineNumber: 128,
                    columnNumber: 17
                }, this)
            }, void 0, false, {
                fileName: "[project]/app/facilities/page.js",
                lineNumber: 127,
                columnNumber: 13
            }, this),
            filteredFacilities.length === 0 && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$core$2f$Box$2f$Box$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Box"], {
                py: 50,
                ta: "center",
                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$Text$2f$Text$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Text"], {
                    c: "dimmed",
                    children: "검색 결과가 없습니다."
                }, void 0, false, {
                    fileName: "[project]/app/facilities/page.js",
                    lineNumber: 143,
                    columnNumber: 21
                }, this)
            }, void 0, false, {
                fileName: "[project]/app/facilities/page.js",
                lineNumber: 142,
                columnNumber: 17
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$components$2f$facilities$2f$FacilityModal$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["FacilityModal"], {
                facility: selectedFacility,
                onClose: ()=>setSelectedFacility(null)
            }, void 0, false, {
                fileName: "[project]/app/facilities/page.js",
                lineNumber: 148,
                columnNumber: 13
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/app/facilities/page.js",
        lineNumber: 48,
        columnNumber: 9
    }, this);
}
function Facilities() {
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Suspense"], {
        fallback: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mantine$2f$core$2f$esm$2f$components$2f$LoadingOverlay$2f$LoadingOverlay$2e$mjs__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["LoadingOverlay"], {
            visible: true
        }, void 0, false, {
            fileName: "[project]/app/facilities/page.js",
            lineNumber: 158,
            columnNumber: 29
        }, void 0),
        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(FacilitiesContent, {}, void 0, false, {
            fileName: "[project]/app/facilities/page.js",
            lineNumber: 159,
            columnNumber: 13
        }, this)
    }, void 0, false, {
        fileName: "[project]/app/facilities/page.js",
        lineNumber: 158,
        columnNumber: 9
    }, this);
}
}),
];

//# sourceMappingURL=_35fd7969._.js.map