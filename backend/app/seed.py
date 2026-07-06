from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from .models import (
    BomItem,
    Material,
    MaterialIssue,
    ProcessRoute,
    ProcessRouteStep,
    Product,
    QualityRecord,
    QualityResult,
    StationTask,
    StationTaskStatus,
    WorkOrder,
    WorkOrderStatus,
    WorkStation,
)


def seed_demo_data(db: Session) -> None:
    if db.query(Product).first():
        return

    # 产品 — 模拟三一泵车产品线
    products = [
        Product(
            code="SY-5288THB",
            name="52米混凝土泵车",
            description="三一重工经典泵车，臂架长度52米",
        ),
        Product(
            code="SY-6210THB",
            name="62米混凝土泵车",
            description="超长臂架泵车，适合高层建筑施工",
        ),
        Product(
            code="SY-HBT6013",
            name="拖式混凝土泵 HBT6013",
            description="拖泵产品，适用于固定工地",
        ),
    ]
    db.add_all(products)
    db.flush()

    # 物料
    materials = [
        Material(code="M-CHASSIS-001", name="底盘总成", unit="套", is_critical=True, stock_qty=12),
        Material(code="M-BOOM-052", name="52米臂架总成", unit="套", is_critical=True, stock_qty=8),
        Material(code="M-PUMP-001", name="混凝土输送泵", unit="台", is_critical=True, stock_qty=15),
        Material(code="M-HYD-001", name="液压系统总成", unit="套", is_critical=False, stock_qty=20),
        Material(code="M-CTRL-001", name="电控系统", unit="套", is_critical=True, stock_qty=3),
        Material(code="M-BOLT-M8", name="M8 螺栓", unit="个", is_critical=False, stock_qty=50000),
        Material(code="M-PIPE-001", name="输送管道", unit="米", is_critical=False, stock_qty=200),
        Material(code="M-TIRE-001", name="工程轮胎", unit="条", is_critical=False, stock_qty=48),
    ]
    db.add_all(materials)
    db.flush()

    # BOM — 52米泵车
    pump_bom = [
        BomItem(product_id=products[0].id, material_id=materials[0].id, quantity=1),
        BomItem(product_id=products[0].id, material_id=materials[1].id, quantity=1),
        BomItem(product_id=products[0].id, material_id=materials[2].id, quantity=1),
        BomItem(product_id=products[0].id, material_id=materials[3].id, quantity=1),
        BomItem(product_id=products[0].id, material_id=materials[4].id, quantity=1),
        BomItem(product_id=products[0].id, material_id=materials[5].id, quantity=1200),
        BomItem(product_id=products[0].id, material_id=materials[6].id, quantity=85),
        BomItem(product_id=products[0].id, material_id=materials[7].id, quantity=6),
    ]
    db.add_all(pump_bom)

    # 工位 — 18号工厂装配线
    stations = [
        WorkStation(code="WS-A01", name="底盘预装工位", line="总装线A", description="底盘上线、轮胎安装"),
        WorkStation(code="WS-A02", name="臂架装配工位", line="总装线A", description="臂架展开、销轴连接"),
        WorkStation(code="WS-A03", name="泵送系统工位", line="总装线A", description="输送泵、管道安装"),
        WorkStation(code="WS-A04", name="液压系统工位", line="总装线A", description="液压管路连接、压力测试"),
        WorkStation(code="WS-A05", name="电控系统工位", line="总装线A", description="线束安装、控制器调试"),
        WorkStation(code="WS-A06", name="整机联调工位", line="总装线A", description="整机功能测试"),
        WorkStation(code="WS-A07", name="终检工位", line="总装线A", description="出厂检验、涂装检查"),
    ]
    db.add_all(stations)
    db.flush()

    # 工艺路线
    route = ProcessRoute(product_id=products[0].id, version="2.1", is_active=True)
    db.add(route)
    db.flush()

    sops = [
        (
            1,
            "1. 确认底盘总成到位\n2. 安装6条工程轮胎，扭矩 450N·m\n3. 检查底盘水平度 ≤ 2mm\n4. 扫码确认关重件",
            "佩戴安全帽，注意起重区域",
        ),
        (
            2,
            "1. 臂架吊装到位\n2. 按序连接各节臂架销轴\n3. 涂抹润滑脂\n4. 臂架展开测试（空载）",
            "臂架下方禁止站人，需2人协同",
        ),
        (
            3,
            "1. 安装混凝土输送泵\n2. 连接输送管道\n3. 管道密封性检查\n4. 泵送系统空载试运行",
            "管道连接处需二次确认",
        ),
        (
            4,
            "1. 安装液压油箱及管路\n2. 连接各执行器\n3. 液压系统保压测试 28MPa\n4. 检查无泄漏",
            "液压油禁止接触皮肤",
        ),
        (
            5,
            "1. 安装线束及传感器\n2. 连接控制器\n3. 上电自检\n4. 参数标定",
            "断电操作，防静电",
        ),
        (
            6,
            "1. 全系统联合调试\n2. 臂架+泵送联动测试\n3. 记录各项参数\n4. 异常处理",
            "调试区域设置警戒线",
        ),
        (
            7,
            "1. 外观检查\n2. 功能终检\n3. 关重件追溯确认\n4. 出具合格证",
            "终检不合格禁止出厂",
        ),
    ]

    for seq, (station_idx, sop, safety) in enumerate(sops, start=1):
        db.add(
            ProcessRouteStep(
                route_id=route.id,
                station_id=stations[station_idx - 1].id,
                sequence=seq,
                sop_content=sop,
                standard_time_min=45,
                safety_notes=safety,
            )
        )

    # 示例工单
    now = datetime.utcnow()
    orders = [
        WorkOrder(
            order_no="WO-20250706-001",
            product_id=products[0].id,
            quantity=1,
            status=WorkOrderStatus.IN_PROGRESS,
            customer="中建三局",
            priority=1,
            planned_start=now - timedelta(hours=4),
            planned_end=now + timedelta(hours=4),
            released_at=now - timedelta(hours=4),
        ),
        WorkOrder(
            order_no="WO-20250706-002",
            product_id=products[0].id,
            quantity=1,
            status=WorkOrderStatus.RELEASED,
            customer="上海建工",
            priority=3,
            planned_start=now + timedelta(hours=2),
            planned_end=now + timedelta(hours=10),
            released_at=now,
        ),
        WorkOrder(
            order_no="WO-20250705-003",
            product_id=products[2].id,
            quantity=2,
            status=WorkOrderStatus.PENDING,
            customer="中铁建工",
            priority=5,
            planned_start=now + timedelta(days=1),
            planned_end=now + timedelta(days=2),
        ),
    ]
    db.add_all(orders)
    db.flush()

    # 为进行中的工单创建工位任务
    wo1_tasks = [
        StationTask(
            work_order_id=orders[0].id,
            station_id=stations[i].id,
            sequence=i + 1,
            sop_content=sops[i][1],
            safety_notes=sops[i][2],
            status=StationTaskStatus.COMPLETED if i < 3 else (
                StationTaskStatus.IN_PROGRESS if i == 3 else StationTaskStatus.WAITING
            ),
            operator="张师傅" if i < 4 else ("李师傅" if i == 3 else None),
            started_at=now - timedelta(hours=4 - i) if i <= 3 else (
                now - timedelta(minutes=30) if i == 3 else None
            ),
            completed_at=now - timedelta(hours=3 - i) if i < 3 else None,
        )
        for i in range(7)
    ]
    db.add_all(wo1_tasks)

    wo2_tasks = [
        StationTask(
            work_order_id=orders[1].id,
            station_id=stations[i].id,
            sequence=i + 1,
            sop_content=sops[i][1],
            safety_notes=sops[i][2],
            status=StationTaskStatus.WAITING,
        )
        for i in range(7)
    ]
    db.add_all(wo2_tasks)

    # 物料配送
    for item in pump_bom[:4]:
        db.add(
            MaterialIssue(
                work_order_id=orders[0].id,
                material_id=item.material_id,
                quantity=item.quantity,
                status="delivered" if item.material_id <= materials[2].id else "pending",
            )
        )

    # 质检记录
    quality_items = [
        ("底盘水平度", "≤ 2mm", QualityResult.PASS),
        ("轮胎扭矩", "450±20 N·m", QualityResult.PASS),
        ("臂架销轴间隙", "≤ 0.5mm", QualityResult.PASS),
        ("液压保压", "28MPa/30min 无泄漏", QualityResult.PENDING),
    ]
    for i, (item, std, result) in enumerate(quality_items):
        db.add(
            QualityRecord(
                work_order_id=orders[0].id,
                station_id=stations[min(i, 6)].id,
                inspector="王质检",
                check_item=item,
                standard=std,
                result=result,
            )
        )

    db.commit()
