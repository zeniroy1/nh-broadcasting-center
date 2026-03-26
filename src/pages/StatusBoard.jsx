import React from 'react';
import { Container, Title, Grid, Card, Text, Group, ThemeIcon, Badge, Divider, List, Box } from '@mantine/core';
import { motion } from 'framer-motion';
import { IconMicrophone, IconAntennaBars5, IconVolume, IconDisc, IconVideo, IconBuildingSkyscraper, IconBuilding } from '@tabler/icons-react';

// Detailed Data Source
const ROOM_DATA = [
    {
        id: 'main',
        building: '본관',
        icon: IconBuilding,
        color: 'indigo', // Changed from blue to indigo for deeper navy feel
        rooms: [
            { name: '대강당', wired: '8', wireless: '8', conf: '-', anthem: '가능', record: '가능', video: '전광판' },
            { name: '중회의실', wired: '4', wireless: '4', conf: '25', anthem: '가능', record: '가능', video: '전광판' },
            { name: '화상회의실', wired: '1 (사회석)', wireless: '2', conf: '31 (고정)', anthem: '가능', record: '가능', video: '전광판' },
            { name: '소회의실', wired: '2', wireless: '2', conf: '-', anthem: '불가', record: '불가', video: '전자칠판' },
            { name: '신토불이', wired: '1', wireless: '2', conf: '-', anthem: '불가', record: '불가', video: '미지원' },
            { name: '두레식당', wired: '1', wireless: '2', conf: '-', anthem: '불가', record: '불가', video: '미지원' },
            { name: '경영전략실', wired: '1', wireless: '2', conf: '21 (고정)', anthem: '불가', record: '불가', video: '미지원' },
            { name: '이동장비', wired: '2', wireless: '4', conf: '-', anthem: '가능', record: '불가', video: '미지원' }
        ]
    },
    {
        id: 'new',
        building: '신관',
        icon: IconBuildingSkyscraper,
        color: 'cyan', // Changed from teal to cyan for better navy contrast
        rooms: [
            { name: '대회의실', wired: '6', wireless: '6', conf: '24', anthem: '가능', record: '가능', video: '전광판' },
            { name: '중회의실', wired: '6', wireless: '3', conf: '20', anthem: '가능', record: '가능', video: '전광판' },
            { name: '1소회의실', wired: '2', wireless: '2', conf: '-', anthem: '불가', record: '가능', video: '전광판' },
            { name: '2소회의실', wired: '5', wireless: '2', conf: '-', anthem: '불가', record: '가능', video: '전광판' },
            { name: '3소회의실', wired: '5', wireless: '2', conf: '-', anthem: '불가', record: '가능', video: '전광판' },
            { name: '경영전략회의실', wired: '2', wireless: '1', conf: '20 (고정)', anthem: '불가', record: '가능', video: '전광판' },
            { name: '행복마루', wired: '1', wireless: '2', conf: '-', anthem: '불가', record: '불가', video: '미지원' },
            { name: '채움마루', wired: '미지원', wireless: '미지원', conf: '-', anthem: '불가', record: '불가', video: '미지원' }
        ]
    }
];

const StatusBoard = () => {
    // Animation variants
    const containerVariants = {
        hidden: { opacity: 0 },
        visible: {
            opacity: 1,
            transition: { staggerChildren: 0.1 }
        }
    };

    const cardVariants = {
        hidden: { y: 30, opacity: 0 },
        visible: {
            y: 0,
            opacity: 1,
            transition: { type: "spring", stiffness: 80, damping: 15 }
        }
    };

    return (
        <Container size="xl" py="xl">
            <motion.div initial="hidden" animate="visible" variants={containerVariants}>

                {/* Header Section */}
                <div style={{ textAlign: 'center', marginBottom: '4rem', marginTop: '1rem' }}>
                    <motion.div
                        initial={{ opacity: 0, y: -20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.8 }}
                    >
                        <Title
                            order={1}
                            style={{
                                fontSize: '2.8rem',
                                marginBottom: '1rem',
                                color: 'var(--color-primary)', // Use theme font color
                                fontWeight: 900,
                                letterSpacing: '-1px'
                            }}
                        >
                            방송장비 이용현황
                        </Title>
                    </motion.div>
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 0.4 }}
                    >
                        {/* Use standard text color for reliable contrast */}
                        <Text style={{ color: 'var(--color-text-muted)' }} size="lg" fw={500}>
                            본관 및 신관의 각 회의실별 방송 장비 보유 현황 및 지원 가능 여부를 확인하세요.
                        </Text>
                    </motion.div>
                </div>

                {/* Building Sections */}
                {ROOM_DATA.map((buildingData, sectionIndex) => (
                    <Box key={buildingData.id} mb={60}>
                        {/* Section Header */}
                        <motion.div
                            initial={{ opacity: 0, x: -20 }}
                            whileInView={{ opacity: 1, x: 0 }}
                            viewport={{ once: true }}
                            transition={{ delay: 0.2 }}
                        >
                            <Group mb="xl" style={{ borderBottom: `2px solid var(--mantine-color-${buildingData.color}-9)`, paddingBottom: '10px' }}>
                                <ThemeIcon size="xl" radius="md" color={buildingData.color} variant="filled">
                                    <buildingData.icon size={24} />
                                </ThemeIcon>
                                {/* Use standard text color */}
                                <Title order={2} size="h1" fw={900} style={{ color: 'var(--color-text)' }}>
                                    {buildingData.building}
                                </Title>
                            </Group>
                        </motion.div>

                        <Grid gutter={30}>
                            {buildingData.rooms.map((room, index) => (
                                <Grid.Col key={`${buildingData.id}-${index}`} span={{ base: 12, md: 6, lg: 4 }}>
                                    <motion.div variants={cardVariants} whileHover={{ y: -8, transition: { duration: 0.2 } }}>
                                        <Card
                                            shadow="sm"
                                            padding="xl"
                                            radius="md"
                                            withBorder
                                            style={{
                                                height: '100%',
                                                borderTop: `4px solid var(--mantine-color-${buildingData.color}-8)`,
                                                backgroundColor: 'var(--color-bg-card)'
                                            }}
                                        >
                                            <Card.Section withBorder inheritPadding py="md" style={{ backgroundColor: `var(--mantine-color-${buildingData.color}-1)` }}>
                                                <Group justify="space-between" align="center">
                                                    {/* Increased size for title */}
                                                    <Text fw={900} style={{ fontSize: '1.5rem', letterSpacing: '-0.5px', color: '#1a1a1a' }}>
                                                        {room.name}
                                                    </Text>
                                                    {room.video !== '미지원' && room.video !== 'X' && (
                                                        <Badge color={buildingData.color} variant="filled" size="lg">
                                                            {room.video}
                                                        </Badge>
                                                    )}
                                                </Group>
                                            </Card.Section>

                                            <Card.Section inheritPadding py="lg">
                                                <Box mb="md">
                                                    {/* Increased size for headers */}
                                                    <Text size="sm" style={{ color: 'var(--color-text-muted)' }} fw={800} mb="sm" tt="uppercase">Audio System</Text>
                                                    <Group grow preventGrowOverflow={false} align="flex-start" mb="xs">
                                                        <EquipmentDetail
                                                            icon={IconMicrophone}
                                                            label="유선 마이크"
                                                            value={room.wired}
                                                            color="indigo"
                                                        />
                                                        <EquipmentDetail
                                                            icon={IconAntennaBars5}
                                                            label="무선 마이크"
                                                            value={room.wireless}
                                                            color="indigo"
                                                        />
                                                    </Group>
                                                    <EquipmentDetail
                                                        icon={IconVolume}
                                                        label="회의용 마이크"
                                                        value={room.conf}
                                                        color="cyan"
                                                        fullWidth
                                                    />
                                                </Box>

                                                <Divider my="md" variant="dashed" />

                                                <Box>
                                                    <Text size="sm" style={{ color: 'var(--color-text-muted)' }} fw={800} mb="sm" tt="uppercase">Support & Video</Text>
                                                    <List spacing="xs" size="sm" center>
                                                        <List.Item icon={<ThemeIcon color="teal" size={24} radius="xl" variant="light"><IconDisc size={14} /></ThemeIcon>}>
                                                            <Group gap="xs">
                                                                <Text size="md" style={{ color: 'var(--color-text-muted)' }} fw={600}>국민의례 지원:</Text>
                                                                <Text size="md" fw={700} c={room.anthem === '가능' ? 'teal.9' : 'gray.6'}>{room.anthem}</Text>
                                                            </Group>
                                                        </List.Item>
                                                        <List.Item icon={<ThemeIcon color="grape" size={24} radius="xl" variant="light"><IconVideo size={14} /></ThemeIcon>}>
                                                            <Group gap="xs">
                                                                <Text size="md" style={{ color: 'var(--color-text-muted)' }} fw={600}>녹음/녹화 지원:</Text>
                                                                <Text size="md" fw={700} c={room.record === '가능' ? 'grape.9' : 'gray.6'}>{room.record}</Text>
                                                            </Group>
                                                        </List.Item>
                                                    </List>
                                                </Box>
                                            </Card.Section>
                                        </Card>
                                    </motion.div>
                                </Grid.Col>
                            ))}
                        </Grid>
                    </Box>
                ))}

                <motion.div variants={cardVariants}>
                    <Text ta="center" mt={20} style={{ color: 'var(--color-text-muted)', borderRadius: '8px' }} size="md" bg="gray.1" py="md">
                        * 본 현황은 2025.09.05 기준입니다. 실제 현황과 다를 수 있으니 정확한 정보는 <Text span fw={800} c="blue.8">방송운영단(5994)</Text>으로 문의 바랍니다.
                    </Text>
                </motion.div>
            </motion.div>
        </Container>
    );
};

// Helper Component for Equipment Details
const EquipmentDetail = ({ icon: Icon, label, value, color, fullWidth }) => {
    const isAvailable = value !== 'X' && value !== '-' && value !== '미지원';
    return (
        <Group gap="xs" style={{ width: fullWidth ? '100%' : 'auto', opacity: isAvailable ? 1 : 0.6 }}>
            <ThemeIcon color={color} variant="light" size="lg" radius="md">
                <Icon size="1.2rem" />
            </ThemeIcon>
            <div>
                {/* Increased sizes for label and value */}
                <Text size="13px" style={{ color: 'var(--color-text-muted)' }} lh={1.2} fw={700}>{label}</Text>
                <Text style={{ fontSize: '1.1rem', color: isAvailable ? 'var(--color-text)' : 'var(--color-text-muted)' }} fw={800}>
                    {value === 'X' || value === '-' ? '미지원' : value}
                </Text>
            </div>
        </Group>
    );
};

export default StatusBoard;
