PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE alembic_version (
        version_num VARCHAR(32) NOT NULL, 
        CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);
INSERT INTO alembic_version VALUES('67d3f4576d73');
CREATE TABLE user (
        id INTEGER NOT NULL, 
        line_id VARCHAR(100) NOT NULL, 
        name VARCHAR(100), 
        picture_url VARCHAR(255), 
        email VARCHAR(120), 
        created_at DATETIME, 
        company_name VARCHAR(200), 
        company_address TEXT, 
        tax_id VARCHAR(20), 
        logo_path VARCHAR(255), 
        PRIMARY KEY (id), 
        UNIQUE (line_id)
);
INSERT INTO user VALUES(1,'Ueb954abce1b8c04d3506619ee9c47567','แอมแปมนะจ๊ะ','https://profile.line-scdn.net/0hkvwtw0cxNFlaDSA0k_hKJipdNzN5fG1Lf2goamoNbGs1OScPfj8uOWwEOGtvNSYNdmp_OGwLbjtWHkM_RFvIbV09aWhmO3ENcm1yvQ',NULL,'2025-05-03 20:06:38.793274',NULL,NULL,NULL,NULL);
INSERT INTO user VALUES(2,'U97b707559139fcad4609d43eda16a43c','Golf ⛳️','https://profile.line-scdn.net/0hwrv3tjTAKF1bSj-4TSBWIisaKzd4O3FPdH8zPmdDJTlicm4IJSo1b2kedT4zfWwNfihlPmlIcW5XWV87RRzUaVx6dWxnfG0JcypuuQ',NULL,'2025-05-03 20:07:47.947912',NULL,NULL,NULL,NULL);
CREATE TABLE bank_account (
        id INTEGER NOT NULL, 
        bank_name VARCHAR(100) NOT NULL, 
        account_number VARCHAR(20) NOT NULL, 
        account_name VARCHAR(200), 
        initial_balance FLOAT, 
        current_balance FLOAT, 
        is_active BOOLEAN, 
        created_at DATETIME, 
        user_id INTEGER NOT NULL, 
        PRIMARY KEY (id), 
        FOREIGN KEY(user_id) REFERENCES user (id)
);
INSERT INTO bank_account VALUES(1,'ธนาคารหลัก','XXXX','บัญชีหลัก',0.0,73898.009999999310819,1,'2025-05-03 20:06:38.833051',1);
INSERT INTO bank_account VALUES(2,'ธนาคารหลัก','XXXX','บัญชีหลัก',0.0,0.0,1,'2025-05-03 20:07:47.979436',2);
CREATE TABLE category (
        id INTEGER NOT NULL, 
        name VARCHAR(100) NOT NULL, 
        type VARCHAR(10) NOT NULL, 
        keywords TEXT, 
        user_id INTEGER NOT NULL, 
        PRIMARY KEY (id), 
        FOREIGN KEY(user_id) REFERENCES user (id)
);
INSERT INTO category VALUES(1,'ค่าคอร์ส','income','ค่าคอร์ส,course,คอร์สเรียน',1);
INSERT INTO category VALUES(2,'ค่าสอนพิเศษตามโรงเรียน','income','สอนพิเศษ,โรงเรียน,tutor,school',1);
INSERT INTO category VALUES(3,'ค่าสอนพิเศษตามบ้าน','income','สอนพิเศษ,ตามบ้าน,บ้าน,home tutor',1);
INSERT INTO category VALUES(4,'ขายสินค้า','income','ขาย,สินค้า,sale,product',1);
INSERT INTO category VALUES(5,'ค่าสมัครสมาชิก','income','สมัคร,สมาชิก,membership,registration',1);
INSERT INTO category VALUES(6,'ค่าหนังสือ/เอกสาร','income','หนังสือ,เอกสาร,book,document',1);
INSERT INTO category VALUES(7,'ค่าสอบ/ทดสอบ','income','สอบ,ทดสอบ,exam,test',1);
INSERT INTO category VALUES(8,'ค่าก่อสร้าง/เฟอร์นิเจอร์','expense','ก่อสร้าง,เฟอร์นิเจอร์,construction,furniture',1);
INSERT INTO category VALUES(9,'ค่าอาหาร','expense','อาหาร,food,restaurant,ร้านอาหาร',1);
INSERT INTO category VALUES(10,'ค่าสาธารณูปโภค','expense','ค่าเช่า,ค่าน้ำ,ค่าไฟ,utilities,rent,water,electricity',1);
INSERT INTO category VALUES(11,'ค่าอุปกรณ์การสอน','expense','อุปกรณ์,การสอน,teaching,materials,stationery',1);
INSERT INTO category VALUES(12,'ค่าเงินเดือน','expense','เงินเดือน,salary,wage,พนักงาน',1);
INSERT INTO category VALUES(13,'ค่าการตลาด/โฆษณา','expense','การตลาด,โฆษณา,marketing,advertising',1);
INSERT INTO category VALUES(14,'ค่าซ่อมบำรุง','expense','ซ่อม,บำรุง,maintenance,repair',1);
INSERT INTO category VALUES(15,'ค่าใช้จ่ายสำนักงาน','expense','สำนักงาน,office,supplies',1);
INSERT INTO category VALUES(16,'ค่าพัฒนาระบบ/IT','expense','คอมพิวเตอร์,IT,software,hardware',1);
INSERT INTO category VALUES(17,'อื่นๆ','income','',1);
INSERT INTO category VALUES(18,'อื่นๆ','expense','',1);
INSERT INTO category VALUES(19,'ค่าคอร์ส','income','ค่าคอร์ส,course,คอร์สเรียน',2);
INSERT INTO category VALUES(20,'ค่าสอนพิเศษตามโรงเรียน','income','สอนพิเศษ,โรงเรียน,tutor,school',2);
INSERT INTO category VALUES(21,'ค่าสอนพิเศษตามบ้าน','income','สอนพิเศษ,ตามบ้าน,บ้าน,home tutor',2);
INSERT INTO category VALUES(22,'ขายสินค้า','income','ขาย,สินค้า,sale,product',2);
INSERT INTO category VALUES(23,'ค่าสมัครสมาชิก','income','สมัคร,สมาชิก,membership,registration',2);
INSERT INTO category VALUES(24,'ค่าหนังสือ/เอกสาร','income','หนังสือ,เอกสาร,book,document',2);
INSERT INTO category VALUES(25,'ค่าสอบ/ทดสอบ','income','สอบ,ทดสอบ,exam,test',2);
INSERT INTO category VALUES(26,'ค่าก่อสร้าง/เฟอร์นิเจอร์','expense','ก่อสร้าง,เฟอร์นิเจอร์,construction,furniture',2);
INSERT INTO category VALUES(27,'ค่าอาหาร','expense','อาหาร,food,restaurant,ร้านอาหาร',2);
INSERT INTO category VALUES(28,'ค่าสาธารณูปโภค','expense','ค่าเช่า,ค่าน้ำ,ค่าไฟ,utilities,rent,water,electricity',2);
INSERT INTO category VALUES(29,'ค่าอุปกรณ์การสอน','expense','อุปกรณ์,การสอน,teaching,materials,stationery',2);
INSERT INTO category VALUES(30,'ค่าเงินเดือน','expense','เงินเดือน,salary,wage,พนักงาน',2);
INSERT INTO category VALUES(31,'ค่าการตลาด/โฆษณา','expense','การตลาด,โ���ษณา,marketing,advertising',2);
INSERT INTO category VALUES(32,'ค่าซ่อมบำรุง','expense','ซ่อม,บำรุง,maintenance,repair',2);
INSERT INTO category VALUES(33,'ค่าใช้จ่ายสำนักงาน','expense','สำนักงาน,office,supplies',2);
INSERT INTO category VALUES(34,'ค่าพัฒนาระบบ/IT','expense','คอมพิวเตอร์,IT,software,hardware',2);
INSERT INTO category VALUES(35,'อื่นๆ','income','',2);
INSERT INTO category VALUES(36,'อื่นๆ','expense','',2);
INSERT INTO category VALUES(37,'จัดการบัญชี','expense','',1);
INSERT INTO category VALUES(38,'การลงทุน','income','',1);
CREATE TABLE invite_token (
        id INTEGER NOT NULL, 
        token VARCHAR(100) NOT NULL, 
        created_by INTEGER NOT NULL, 
        created_at DATETIME, 
        used BOOLEAN, 
        used_by INTEGER, 
        PRIMARY KEY (id), 
        FOREIGN KEY(created_by) REFERENCES user (id), 
        FOREIGN KEY(used_by) REFERENCES user (id), 
        UNIQUE (token)
);
INSERT INTO invite_token VALUES(1,'b49b5b0d-097f-43d7-be2e-35d95ebd8c2e',1,'2025-05-03 20:06:44.282684',0,NULL);
INSERT INTO invite_token VALUES(2,'5dd6317e-2b93-4819-9d01-6370ded9004b',1,'2025-05-03 20:56:03.382310',0,NULL);
INSERT INTO invite_token VALUES(3,'7508ced5-9577-4b3e-9cb9-b211f7357c67',1,'2025-05-03 20:56:07.443534',0,NULL);
CREATE TABLE import_history (
        id INTEGER NOT NULL, 
        batch_id VARCHAR(50) NOT NULL, 
        filename VARCHAR(255) NOT NULL, 
        bank_type VARCHAR(50) NOT NULL, 
        import_date DATETIME, 
        transaction_count INTEGER, 
        total_amount FLOAT, 
        status VARCHAR(20), 
        user_id INTEGER NOT NULL, 
        bank_account_id INTEGER, 
        PRIMARY KEY (id), 
        FOREIGN KEY(bank_account_id) REFERENCES bank_account (id), 
        FOREIGN KEY(user_id) REFERENCES user (id), 
        UNIQUE (batch_id)
);
INSERT INTO import_history VALUES(1,'722e1c15-3acc-4f93-8871-e928a3e546a5','codelab acc29apr.xlsx','scb','2025-05-03 20:42:26.856329',151,2745474.6899999999442,'completed',1,1);
CREATE TABLE IF NOT EXISTS "transaction" (
        id INTEGER NOT NULL, 
        amount FLOAT NOT NULL, 
        description TEXT, 
        transaction_date DATE NOT NULL, 
        type VARCHAR(10) NOT NULL, 
        status VARCHAR(20), 
        transaction_time TIME, 
        completed_date DATETIME, 
        source VARCHAR(20), 
        bank_account_id INTEGER, 
        bank_reference VARCHAR(100), 
        import_batch_id VARCHAR(50), 
        created_at DATETIME, 
        user_id INTEGER NOT NULL, 
        category_id INTEGER NOT NULL, 
        PRIMARY KEY (id), 
        FOREIGN KEY(bank_account_id) REFERENCES bank_account (id), 
        FOREIGN KEY(category_id) REFERENCES category (id), 
        FOREIGN KEY(user_id) REFERENCES user (id)
);
INSERT INTO "transaction" VALUES(1,62510.0,'โอ���ไป SCB x9870 นาย อานพ บุญนำสุขสกุล    (ค่าติดตั้งแอร์ร้านพระราม 2 (งวดแรก))','2025-02-01','expense','completed','01:33:00.000000','2025-05-03 20:42:26.825891','import',1,'01:33','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866146',1,8);
INSERT INTO "transaction" VALUES(2,162069.54000000000815,'โอนไป SCB x1694 นาย ตรีฉัตร จนิลรัตนะพงษ (ค่างานตกแต่งร้านพระราม 2 (งวดที่ 3) CodeLab)','2025-02-01','expense','completed','01:34:00.000000','2025-05-03 20:42:26.826779','import',1,'01:34','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866171',1,8);
INSERT INTO "transaction" VALUES(3,8500.0,'กสิกรไทย (KBANK) /X103885               ','2025-02-02','income','completed','19:26:00.000000','2025-05-03 20:42:26.826983','import',1,'19:26','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866184',1,1);
INSERT INTO "transaction" VALUES(4,8483.9999999999999996,'โอนไป SCB x9410 บริษัท โฮม โปรดักส์ เซ็น (ค่าพัดลมดูดอากาศร้านพระราม2)','2025-02-05','expense','completed','15:57:00.000000','2025-05-03 20:42:26.827174','import',1,'15:57','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866196',1,8);
INSERT INTO "transaction" VALUES(5,9341.0000000000000001,'Transfer to SCB x8533 นางสาว มัลลิกา สุด','2025-02-06','expense','completed','08:28:00.000000','2025-05-03 20:42:26.827285','import',1,'08:28','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866206',1,8);
INSERT INTO "transaction" VALUES(6,9591.0000000000000001,'Transfer to SCB x8533 นางสาว มัลลิกา สุด','2025-02-06','expense','completed','08:29:00.000000','2025-05-03 20:42:26.827416','import',1,'08:29','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866214',1,8);
INSERT INTO "transaction" VALUES(7,18579.999999999999999,'Transfer to SCB x8533 นางสาว มัลลิกา สุด','2025-02-06','expense','completed','09:08:00.000000','2025-05-03 20:42:26.827548','import',1,'09:08','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866223',1,8);
INSERT INTO "transaction" VALUES(8,7559.9399999999995999,'โอนไป SCB x0820 บริษัท สหัสวรรษ ไล้ท์ติ้ (ค่าหลอดไฟร้านพระราม 2)','2025-02-10','expense','completed','12:17:00.000000','2025-05-03 20:42:26.827688','import',1,'12:17','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866231',1,8);
INSERT INTO "transaction" VALUES(9,21349.999999999999999,'โอนไป SCB x1694 นาย ตรีฉัตร จนิลรัตนะพงษ (ค่าตู้โหลดไฟและเบรกเกอร์ร้านพระราม2 CodeLab)','2025-02-10','expense','completed','12:18:00.000000','2025-05-03 20:42:26.827813','import',1,'12:18','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866240',1,8);
INSERT INTO "transaction" VALUES(10,29899.999999999999999,'กสิกรไทย (KBANK) /X122125               ','2025-02-11','income','completed','10:40:00.000000','2025-05-03 20:42:26.827931','import',1,'10:40','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866248',1,1);
INSERT INTO "transaction" VALUES(11,22211.999999999999999,'Transfer to SCB x8533 นางสาว มัลลิกา สุด','2025-02-11','expense','completed','13:23:00.000000','2025-05-03 20:42:26.828053','import',1,'13:23','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866259',1,8);
INSERT INTO "transaction" VALUES(12,101990.0,'โอนไป SCB x9870 นาย อานพ บุญนำสุขสกุล    (ค่าแอร์ร้านพระราม2(งวดสุดท้าย))','2025-02-14','expense','completed','15:05:00.000000','2025-05-03 20:42:26.828156','import',1,'15:05','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866268',1,8);
INSERT INTO "transaction" VALUES(13,10669.999999999999999,'โอนไป SCB x1694 นาย ตรีฉัตร จนิลรัตนะพงษ (ค่าทำป้ายPlaswood ร้านพระราม2 CodeLab)','2025-02-15','expense','completed','17:33:00.000000','2025-05-03 20:42:26.828275','import',1,'17:33','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866276',1,8);
INSERT INTO "transaction" VALUES(14,7489.9999999999999997,'โอนไป KBANK x0739 บจก. เบทเทอร์ ช้อยส์ . (water 100pack)','2025-02-17','expense','completed','09:12:00.000000','2025-05-03 20:42:26.828385','import',1,'09:12','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866286',1,9);
INSERT INTO "transaction" VALUES(15,5.0,'ค่าธรรมเนียมโอนไป KBANK x0739 บจก. เบทเท (water 100pack)','2025-02-17','expense','completed','09:12:00.000000','2025-05-03 20:42:26.828510','import',1,'09:12','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866297',1,9);
INSERT INTO "transaction" VALUES(16,5.0,'Transfer fee KBANK x8092 MR. Pratchaya S','2025-02-19','expense','completed','15:56:00.000000','2025-05-03 20:42:26.828627','import',1,'15:56','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866308',1,8);
INSERT INTO "transaction" VALUES(17,37798.0,'Transfer to KBANK x8092 MR. Pratchaya Su','2025-02-19','expense','completed','15:56:00.000000','2025-05-03 20:42:26.828754','import',1,'15:56','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866317',1,8);
INSERT INTO "transaction" VALUES(18,29899.999999999999999,'กสิกรไทย (KBANK) /X482113               ','2025-02-19','income','completed','17:11:00.000000','2025-05-03 20:42:26.828886','import',1,'17:11','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866325',1,1);
INSERT INTO "transaction" VALUES(19,12899.999999999999999,'กสิกรไทย (KBANK) /X585664               ','2025-02-20','income','completed','12:23:00.000000','2025-05-03 20:42:26.829016','import',1,'12:23','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866333',1,1);
INSERT INTO "transaction" VALUES(20,29899.999999999999999,'กรุงเทพ (BBL) /X434181                  ','2025-02-20','income','completed','15:47:00.000000','2025-05-03 20:42:26.829155','import',1,'15:47','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866341',1,1);
INSERT INTO "transaction" VALUES(21,29899.999999999999999,'กรุงศรีอยุธยา (BAY) /X668142            ','2025-02-21','income','completed','14:37:00.000000','2025-05-03 20:42:26.829310','import',1,'14:37','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866349',1,1);
INSERT INTO "transaction" VALUES(22,29899.999999999999999,'รับโอนจาก SCB x9642 นาง ปูรณี กรรณสูต   ','2025-02-22','income','completed','10:57:00.000000','2025-05-03 20:42:26.829455','import',1,'10:57','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866358',1,1);
INSERT INTO "transaction" VALUES(23,29899.999999999999999,'กสิกรไทย (KBANK) /X417927               ','2025-02-22','income','completed','13:49:00.000000','2025-05-03 20:42:26.829593','import',1,'13:49','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866366',1,1);
INSERT INTO "transaction" VALUES(24,24249.999999999999999,'โอนไป SCB x1694 นาย ตรีฉัตร จนิลรัตนะพงษ (ค่างานลามิเนตเพิ่มเติมร้านพระราม 2 CodeLab)','2025-02-22','expense','completed','13:59:00.000000','2025-05-03 20:42:26.829723','import',1,'13:59','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866374',1,8);
INSERT INTO "transaction" VALUES(25,3102.3000000000001818,'โอนไป KBANK x4021 บจก. กรีน ไลท์ แอนด์ เ (ค่าธงร้าน Codelab พระราม 2)','2025-02-22','expense','completed','14:00:00.000000','2025-05-03 20:42:26.829866','import',1,'14:00','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866383',1,8);
INSERT INTO "transaction" VALUES(26,5.0,'ค่าธรรมเนียมโอนไป KBANK x4021 บจก. กรีน  (ค่าธงร้าน Codelab พระราม 2)','2025-02-22','expense','completed','14:00:00.000000','2025-05-03 20:42:26.830002','import',1,'14:00','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866391',1,8);
INSERT INTO "transaction" VALUES(27,21406.930000000000291,'โอนไป SCB x1694 นาย ตรีฉัตร จนิลรัตนะพงษ (ค่างานตกแต่งภายใน ผนัง ไฟ ทาสี-(สุดท้าย) CodeLab)','2025-02-22','expense','completed','14:00:00.000000','2025-05-03 20:42:26.830144','import',1,'14:00','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866399',1,8);
INSERT INTO "transaction" VALUES(28,29899.999999999999999,'กสิกรไทย (KBANK) /X786484               ','2025-02-22','income','completed','21:12:00.000000','2025-05-03 20:42:26.830275','import',1,'21:12','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866407',1,1);
INSERT INTO "transaction" VALUES(29,29899.999999999999999,'กรุงเทพ (BBL) /X670554                  ','2025-02-22','income','completed','22:44:00.000000','2025-05-03 20:42:26.830423','import',1,'22:44','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866415',1,1);
INSERT INTO "transaction" VALUES(30,29899.999999999999999,'กรุงเทพ (BBL) /X608071                  ','2025-02-22','income','completed','22:55:00.000000','2025-05-03 20:42:26.830554','import',1,'22:55','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866424',1,1);
INSERT INTO "transaction" VALUES(31,25799.999999999999999,'กสิกรไทย (KBANK) /X883078               ','2025-02-23','income','completed','09:27:00.000000','2025-05-03 20:42:26.830698','import',1,'09:27','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866436',1,1);
INSERT INTO "transaction" VALUES(32,22799.999999999999999,'รับโอนจาก SCB x0428 นางสาว เพชรชมพู พงษ์','2025-02-23','income','completed','11:46:00.000000','2025-05-03 20:42:26.830822','import',1,'11:46','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866443',1,1);
INSERT INTO "transaction" VALUES(33,25799.999999999999999,'กรุงเทพ (BBL) /X709498                  ','2025-02-23','income','completed','11:59:00.000000','2025-05-03 20:42:26.831124','import',1,'11:59','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866452',1,1);
INSERT INTO "transaction" VALUES(34,22799.999999999999999,'รับโอนจาก SCB x4582 นาย สมศักดิ์ เจริญคุ','2025-02-23','income','completed','12:03:00.000000','2025-05-03 20:42:26.831286','import',1,'12:03','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866460',1,1);
INSERT INTO "transaction" VALUES(35,19800.0,'ออมสิน (GSB) /X655530                   ','2025-02-23','income','completed','12:34:00.000000','2025-05-03 20:42:26.831432','import',1,'12:34','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866471',1,1);
INSERT INTO "transaction" VALUES(36,13899.999999999999999,'รับโอนจาก SCB x8641 นางสาว สุริษา ผุดผ่อ','2025-02-23','income','completed','14:58:00.000000','2025-05-03 20:42:26.831561','import',1,'14:58','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866482',1,1);
INSERT INTO "transaction" VALUES(37,12899.999999999999999,'ทหารไทยธนชาต (TTB) /X001648             ','2025-02-23','income','completed','15:25:00.000000','2025-05-03 20:42:26.831695','import',1,'15:25','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866492',1,1);
INSERT INTO "transaction" VALUES(38,29899.999999999999999,'กสิกรไทย (KBANK) /X083727               ','2025-02-23','income','completed','15:41:00.000000','2025-05-03 20:42:26.831832','import',1,'15:41','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866503',1,1);
INSERT INTO "transaction" VALUES(39,27799.999999999999999,'รับโอนจาก SCB x5454 นางสาว ณธกาญจน์ นิติ','2025-02-23','income','completed','16:19:00.000000','2025-05-03 20:42:26.831965','import',1,'16:19','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866514',1,1);
INSERT INTO "transaction" VALUES(40,12899.999999999999999,'รับโอนจาก SCB x6643 นาย อิทธินันต์ อักษร','2025-02-23','income','completed','16:37:00.000000','2025-05-03 20:42:26.832110','import',1,'16:37','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866523',1,1);
INSERT INTO "transaction" VALUES(41,26800.0,'กสิกรไทย (KBANK) /X999168               ','2025-02-23','income','completed','18:01:00.000000','2025-05-03 20:42:26.832270','import',1,'18:01','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866531',1,1);
INSERT INTO "transaction" VALUES(42,39700.0,'รับโอนจาก SCB x1620 นาย กำธน ลีเลิศพันธ์','2025-02-23','income','completed','23:50:00.000000','2025-05-03 20:42:26.832402','import',1,'23:50','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866539',1,1);
INSERT INTO "transaction" VALUES(43,29899.999999999999999,'กสิกรไทย (KBANK) /X387053               ','2025-02-24','income','completed','12:01:00.000000','2025-05-03 20:42:26.832531','import',1,'12:01','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866547',1,1);
INSERT INTO "transaction" VALUES(44,1819.0,'โอนไป KBANK x0309 บจก. เอ็ม วอเตอร์      (ค่าบล็อกสกรีนขวดน้ำ)','2025-02-25','expense','completed','16:12:00.000000','2025-05-03 20:42:26.832664','import',1,'16:12','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866556',1,8);
INSERT INTO "transaction" VALUES(45,5.0,'ค่าธรรมเนียมโอนไป KBANK x0309 บจก. เอ็ม  (ค่าบล็อกสกรีนขวดน้ำ)','2025-02-25','expense','completed','16:12:00.000000','2025-05-03 20:42:26.832798','import',1,'16:12','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866564',1,8);
INSERT INTO "transaction" VALUES(46,168230.0,'โอนไป SCB x9741 บริษัท เอจี ดราก้อน จำกั (โอนคืนให้ AG ค่าทำร้าน CodeLab (เนื่องจาก AG จ่ายให้ตรีฉัตรไปก่อน))','2025-02-28','expense','completed','05:59:00.000000','2025-05-03 20:42:26.832938','import',1,'05:59','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866572',1,8);
INSERT INTO "transaction" VALUES(47,21000.0099999999984,'IBFT 270422003412 342939035ed44e5ba41b9d (เงินเดือนพนักงาน (02/68))','2025-02-28','expense','completed','13:02:00.000000','2025-05-03 20:42:26.833076','import',1,'13:02','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866580',1,12);
INSERT INTO "transaction" VALUES(48,7500.0,'Transfer to SCB x1318 นางสาว แพรวรุ่ง ปร (เงินเดือนคุณแพรว-(02/68))','2025-02-28','expense','completed','13:03:00.000000','2025-05-03 20:42:26.833182','import',1,'13:03','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866588',1,12);
INSERT INTO "transaction" VALUES(49,29899.999999999999999,'กรุงเทพ (BBL) /X217404                  ','2025-02-28','income','completed','18:51:00.000000','2025-05-03 20:42:26.833322','import',1,'18:51','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866597',1,1);
INSERT INTO "transaction" VALUES(50,29899.999999999999999,'รับโอนจาก SCB x2273 นาง ภาณิศา จัก���ไพวงศ','2025-02-28','income','completed','19:31:00.000000','2025-05-03 20:42:26.833447','import',1,'19:31','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866607',1,1);
INSERT INTO "transaction" VALUES(51,29899.999999999999999,'กรุงศรีอยุธยา (BAY) /X993541            ','2025-03-01','income','completed','14:39:00.000000','2025-05-03 20:42:26.833585','import',1,'14:39','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866615',1,1);
INSERT INTO "transaction" VALUES(52,23199.999999999999999,'Transfer to SCB x8533 นางสาว มัลลิกา สุด','2025-03-02','expense','completed','10:43:00.000000','2025-05-03 20:42:26.833735','import',1,'10:43','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866626',1,8);
INSERT INTO "transaction" VALUES(53,16900.0,'กสิกรไทย (KBANK) /X008637               ','2025-03-02','income','completed','10:51:00.000000','2025-05-03 20:42:26.833867','import',1,'10:51','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866637',1,1);
INSERT INTO "transaction" VALUES(54,5.0,'ค่าธรรมเนียมโอนไป TTB x9460 นาย ยุทธนา เ (VEX and whalesbot 1st and 2nd goods)','2025-03-04','expense','completed','09:25:00.000000','2025-05-03 20:42:26.834147','import',1,'09:25','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866648',1,8);
INSERT INTO "transaction" VALUES(55,224523.47000000000116,'โอนไป TTB x9460 นาย ยุทธนา เทียนธรรมชาติ (VEX and whalesbot 1st and 2nd goods)','2025-03-04','expense','completed','09:25:00.000000','2025-05-03 20:42:26.834283','import',1,'09:25','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866659',1,8);
INSERT INTO "transaction" VALUES(56,5.0,'Transfer fee KBANK x2966 MS. Kwanruen Ko','2025-03-05','expense','completed','13:31:00.000000','2025-05-03 20:42:26.834418','import',1,'13:31','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866670',1,8);
INSERT INTO "transaction" VALUES(57,1539.9999999999999999,'Transfer to KBANK x2966 MS. Kwanruen Kon','2025-03-05','expense','completed','13:31:00.000000','2025-05-03 20:42:26.834547','import',1,'13:31','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866681',1,8);
INSERT INTO "transaction" VALUES(58,7226.4999999999999999,'โอนไป SCB x1694 นาย ตรีฉัตร จนิลรัตนะพงษ (ค่างานเพิ่มเติมชั้น 2 ติดตั้งไฟ-ร้านพระ2 CodeLab)','2025-03-05','expense','completed','15:56:00.000000','2025-05-03 20:42:26.834676','import',1,'15:56','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866692',1,8);
INSERT INTO "transaction" VALUES(59,21406.930000000000291,'โอนไป SCB x1694 นาย ตรีฉัตร จนิลรัตนะพงษ (ค่างานตกแต่ง ภายใน กั้นผนังร้านพระราม 2 CodeLab)','2025-03-05','expense','completed','15:57:00.000000','2025-05-03 20:42:26.834811','import',1,'15:57','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866699',1,8);
INSERT INTO "transaction" VALUES(60,10.0,'PromptPay fee x8383 MISSMANLIKA APISAKMO','2025-03-06','expense','completed','10:38:00.000000','2025-05-03 20:42:26.834944','import',1,'10:38','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866710',1,8);
INSERT INTO "transaction" VALUES(61,5500.0,'PromptPay to x8383 MISSMANLIKA APISAKMON','2025-03-06','expense','completed','10:38:00.000000','2025-05-03 20:42:26.835111','import',1,'10:38','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866722',1,8);
INSERT INTO "transaction" VALUES(62,4400.0,'Transfer to SCB x8533 นางสาว มัลลิกา สุด','2025-03-06','expense','completed','17:54:00.000000','2025-05-03 20:42:26.835249','import',1,'17:54','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866733',1,8);
INSERT INTO "transaction" VALUES(63,15569.999999999999999,'Transfer to KBANK x5539 O.K.ELECTRONICS ','2025-03-08','expense','completed','05:17:00.000000','2025-05-03 20:42:26.835379','import',1,'05:17','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866744',1,8);
INSERT INTO "transaction" VALUES(64,5.0,'Transfer fee KBANK x5539 O.K.ELECTRONICS','2025-03-08','expense','completed','05:17:00.000000','2025-05-03 20:42:26.835509','import',1,'05:17','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866755',1,8);
INSERT INTO "transaction" VALUES(65,484.00000000000000001,'โอนไป SCB x0583 นางสาว ธัญวรัตน์ รุ่งโรจ (ค่าชุดปฐมพยาบาลกล่องยารักษา)','2025-03-08','expense','completed','12:16:00.000000','2025-05-03 20:42:26.835656','import',1,'12:16','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866766',1,8);
INSERT INTO "transaction" VALUES(66,2519.9999999999999999,'โอนไป SCB x0257 บริษัท ทิงค์เน็ต จำกัด  ','2025-03-08','expense','completed','15:55:00.000000','2025-05-03 20:42:26.835789','import',1,'15:55','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866776',1,37);
INSERT INTO "transaction" VALUES(67,5.0,'ค่าธรรมเนียมโอนไป KBANK x5539 หจก. โอ.เค (กล้องวงจรปิด)','2025-03-09','expense','completed','18:08:00.000000','2025-05-03 20:42:26.835928','import',1,'18:08','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866788',1,8);
INSERT INTO "transaction" VALUES(68,15569.999999999999999,'โอนไป KBANK x5539 หจก. โอ.เค.อิเลคทรอนิก (กล้องวงจรปิด)','2025-03-09','expense','completed','18:08:00.000000','2025-05-03 20:42:26.836064','import',1,'18:08','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866797',1,8);
INSERT INTO "transaction" VALUES(69,1.0,'รับชำระค่าสินค้าและบริการ CrossBank     ','2025-03-10','income','completed','22:59:00.000000','2025-05-03 20:42:26.836192','import',1,'22:59','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866805',1,7);
INSERT INTO "transaction" VALUES(70,15569.999999999999999,'กสิกรไทย (KBANK) /X755539               ','2025-03-11','income','completed','08:40:00.000000','2025-05-03 20:42:26.836326','import',1,'08:40','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866813',1,1);
INSERT INTO "transaction" VALUES(71,20970.0,'กสิกรไทย (KBANK) /X085170               ','2025-03-11','income','completed','16:59:00.000000','2025-05-03 20:42:26.836464','import',1,'16:59','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866821',1,1);
INSERT INTO "transaction" VALUES(72,5417.3599999999996726,'โอนไป KBANK x7784 บจก. ทีพีไอ.อิมปอร์ต-เ (ขนส่ง 2รอบ)','2025-03-13','expense','completed','11:00:00.000000','2025-05-03 20:42:26.836602','import',1,'11:00','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866830',1,11);
INSERT INTO "transaction" VALUES(73,5.0,'ค่าธรรมเนียมโอนไป KBANK x7784 บจก. ทีพีไ (ขนส่ง 2รอบ)','2025-03-13','expense','completed','11:00:00.000000','2025-05-03 20:42:26.836732','import',1,'11:00','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866838',1,11);
INSERT INTO "transaction" VALUES(74,37560.999999999999999,'โอนไป SCB x0562 นางสาว ธัญวรัตน์ รุ่งโรจ (ค่าซื้อเครื่องใช้สำนักงาน IKEA-(488&523))','2025-03-13','expense','completed','16:44:00.000000','2025-05-03 20:42:26.836863','import',1,'16:44','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866846',1,15);
INSERT INTO "transaction" VALUES(75,30590.069999999999709,'โอนไป SCB x0562 นางสาว ธัญวรัตน์ รุ่งโรจ (ค่า VEX GO kit 4 Sets)','2025-03-13','expense','completed','16:53:00.000000','2025-05-03 20:42:26.836992','import',1,'16:53','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866854',1,11);
INSERT INTO "transaction" VALUES(76,5.0,'ค่าธรรมเนียมโอนไป KTB x4315 นายปุณณวัฒน์','2025-03-15','expense','completed','09:35:00.000000','2025-05-03 20:42:26.837122','import',1,'09:35','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866862',1,18);
INSERT INTO "transaction" VALUES(77,75.999999999999999999,'โอนไป KTB x4315 นายปุณณวัฒน์ นนทนาคชีวิน','2025-03-15','expense','completed','09:35:00.000000','2025-05-03 20:42:26.837258','import',1,'09:35','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866870',1,15);
INSERT INTO "transaction" VALUES(78,16900.0,'กรุงไทย (KTB) /X812478                  ','2025-03-15','income','completed','10:25:00.000000','2025-05-03 20:42:26.837403','import',1,'10:25','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866878',1,1);
INSERT INTO "transaction" VALUES(79,1304.0,'โอนไป SCB x8533 นางสาว มัลลิกา สุดใจดี  ','2025-03-15','expense','completed','11:28:00.000000','2025-05-03 20:42:26.837530','import',1,'11:28','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866886',1,15);
INSERT INTO "transaction" VALUES(80,74730.350000000005821,'CREDIT CARD DIVISION(EDC)               ','2025-03-16','income','completed','02:48:00.000000','2025-05-03 20:42:26.837671','import',1,'02:48','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866894',1,1);
INSERT INTO "transaction" VALUES(81,2910.0,'โอนไป KBANK x2362 น.ส. อริศรา หล้าที     (ค่าบริการทำบัญชี-CodeLab (02/68))','2025-03-17','expense','completed','12:14:00.000000','2025-05-03 20:42:26.837813','import',1,'12:14','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866903',1,16);
INSERT INTO "transaction" VALUES(82,5.0,'ค่าธรรมเนียมโอนไป KBANK x2362 น.ส. อริศร (ค่าบริการทำบัญชี-CodeLab (02/68))','2025-03-17','expense','completed','12:14:00.000000','2025-05-03 20:42:26.837939','import',1,'12:14','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866911',1,16);
INSERT INTO "transaction" VALUES(83,15.0,'จ่ายบิล REVENUE DEPARTMENT (กรมสร        (ค่าภงด 3&53-CodeLab-(02-68))','2025-03-17','expense','completed','12:15:00.000000','2025-05-03 20:42:26.838080','import',1,'12:15','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866919',1,16);
INSERT INTO "transaction" VALUES(84,6798.0299999999997452,'จ่ายบิล REVENUE DEPARTMENT (กรมสร        (ค่าภงด 3&53-CodeLab-(02-68))','2025-03-17','expense','completed','12:15:00.000000','2025-05-03 20:42:26.838212','import',1,'12:15','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866927',1,16);
INSERT INTO "transaction" VALUES(85,1455.0,'โอนไป SCB x1694 นาย ตรีฉัตร จนิลรัตนะพงษ (ค่างานการเก็บซ่อมประตูกระจกร้านพระราม 2 CodeLab)','2025-03-17','expense','completed','13:03:00.000000','2025-05-03 20:42:26.838340','import',1,'13:03','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866935',1,8);
INSERT INTO "transaction" VALUES(86,8024.9999999999999996,'โอนไป SCB x3507 บริษัท แมงโก้ ลอจิก จำกั','2025-03-19','expense','completed','11:26:00.000000','2025-05-03 20:42:26.838474','import',1,'11:26','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866944',1,11);
INSERT INTO "transaction" VALUES(87,14364.999999999999999,'รับโอนจาก SCB x5262 นาย กิตติภูมิ ทรงเศร','2025-03-19','income','completed','11:44:00.000000','2025-05-03 20:42:26.838607','import',1,'11:44','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866953',1,1);
INSERT INTO "transaction" VALUES(88,14364.999999999999999,'กสิกรไทย (KBANK) /X031412               ','2025-03-19','income','completed','11:47:00.000000','2025-05-03 20:42:26.838719','import',1,'11:47','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866963',1,1);
INSERT INTO "transaction" VALUES(89,14364.999999999999999,'รับโอนจาก SCB x7139 นางพิชามญชุ์ ปรองดอง','2025-03-19','income','completed','12:09:00.000000','2025-05-03 20:42:26.838827','import',1,'12:09','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866972',1,1);
INSERT INTO "transaction" VALUES(90,6989.9999999999999997,'กรุงศรีอยุธยา (BAY) /X366153            ','2025-03-20','income','completed','18:05:00.000000','2025-05-03 20:42:26.838947','import',1,'18:05','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866980',1,1);
INSERT INTO "transaction" VALUES(91,16900.0,'รับโอนจาก SCB x2324 นางสาว วนิดา ตรีระพง','2025-03-22','income','completed','11:00:00.000000','2025-05-03 20:42:26.839123','import',1,'11:00','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866988',1,1);
INSERT INTO "transaction" VALUES(92,49514.940000000002328,'CREDIT CARD DIVISION(EDC)               ','2025-03-23','income','completed','01:20:00.000000','2025-05-03 20:42:26.839233','import',1,'01:20','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.866997',1,1);
INSERT INTO "transaction" VALUES(93,12398.219999999999345,'CREDIT CARD DIVISION(EDC)               ','2025-03-26','income','completed','01:44:00.000000','2025-05-03 20:42:26.839345','import',1,'01:44','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.867059',1,1);
INSERT INTO "transaction" VALUES(94,769.99999999999999998,'โอนไปพร้อมเพย์ x3435 นาย อธาวิน กาแก้ว  ','2025-03-26','expense','completed','17:32:00.000000','2025-05-03 20:42:26.839469','import',1,'17:32','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.867071',1,18);
INSERT INTO "transaction" VALUES(95,10.0,'ค่าธรรมเนียมพร้อมเพย์ x3435 นาย อธาวิน ก','2025-03-26','expense','completed','17:32:00.000000','2025-05-03 20:42:26.839587','import',1,'17:32','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.867080',1,18);
INSERT INTO "transaction" VALUES(96,5.0,'ค่าธรรมเนียมโอนไป KBANK x2362 น.ส. อริศร','2025-03-26','expense','completed','17:52:00.000000','2025-05-03 20:42:26.839694','import',1,'17:52','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.867088',1,18);
INSERT INTO "transaction" VALUES(97,3000.0,'โอนไป KBANK x2362 น.ส. อริศรา หล้าที    ','2025-03-26','expense','completed','17:52:00.000000','2025-05-03 20:42:26.839803','import',1,'17:52','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.867096',1,11);
INSERT INTO "transaction" VALUES(98,90.0,'รับโอนจาก SCB x9197 นางสาว อริศรา หล้าที','2025-03-27','income','completed','10:55:00.000000','2025-05-03 20:42:26.839913','import',1,'10:55','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.867104',1,17);
INSERT INTO "transaction" VALUES(99,1000.0,'กสิกรไทย (KBANK) /X031412               ','2025-03-27','income','completed','10:56:00.000000','2025-05-03 20:42:26.840027','import',1,'10:56','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.867112',1,1);
INSERT INTO "transaction" VALUES(100,47869.980000000003201,'IBFT 270422003412 50aef03eea154c5a9bd20b (เงินเดือนพนักงาน (03/68))','2025-03-28','expense','completed','17:25:00.000000','2025-05-03 20:42:26.840166','import',1,'17:25','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.867120',1,12);
INSERT INTO "transaction" VALUES(101,19175.0,'โอนไป SCB x1318 นางสาว แพรวรุ่ง ประทีป   (ค่าจ้าง (คุณแพรว) เดือน 03/68)','2025-03-28','expense','completed','17:25:00.000000','2025-05-03 20:42:26.840314','import',1,'17:25','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.867129',1,8);
INSERT INTO "transaction" VALUES(102,5000.0,'กสิกรไทย (KBANK) /X085170               ','2025-03-29','income','completed','12:26:00.000000','2025-05-03 20:42:26.840444','import',1,'12:26','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.867137',1,1);
INSERT INTO "transaction" VALUES(103,3549.5199999999999817,'โอนไป KBANK x4555 บจก. ทีพีไอ.อิมปอร์ต-เ (ค่าขนส่งชิปปิ้ง TPI)','2025-03-30','expense','completed','06:57:00.000000','2025-05-03 20:42:26.840589','import',1,'06:57','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.867145',1,11);
INSERT INTO "transaction" VALUES(104,5.0,'ค่าธรรมเนียมโอนไป KBANK x4555 บจก. ทีพีไ (ค่าขนส่งชิปปิ้ง TPI)','2025-03-30','expense','completed','06:57:00.000000','2025-05-03 20:42:26.840713','import',1,'06:57','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.867154',1,11);
INSERT INTO "transaction" VALUES(105,15299.999999999999999,'รับโอนจาก SCB x5660 บริษัท บีน่าโรโบติกส','2025-03-30','income','completed','07:28:00.000000','2025-05-03 20:42:26.840830','import',1,'07:28','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.867162',1,1);
INSERT INTO "transaction" VALUES(106,156939.70999999999185,'โอนไป TTB x9460 นาย ยุทธนา เทียนธรรมชาติ (VEX 2nd order 33460.78 RMB)','2025-03-30','expense','completed','07:29:00.000000','2025-05-03 20:42:26.840953','import',1,'07:29','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.867170',1,11);
INSERT INTO "transaction" VALUES(107,5.0,'ค่าธรรมเนียมโอนไป TTB x9460 นาย ยุทธนา เ (VEX 2nd order 33460.78 RMB)','2025-03-30','expense','completed','07:29:00.000000','2025-05-03 20:42:26.841098','import',1,'07:29','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.867179',1,11);
INSERT INTO "transaction" VALUES(108,150.99999999999999999,'โอนไป SCB x8533 นางสาว มัลลิกา สุดใจดี  ','2025-03-30','expense','completed','11:06:00.000000','2025-05-03 20:42:26.841234','import',1,'11:06','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.867187',1,18);
INSERT INTO "transaction" VALUES(109,3746.9999999999999999,'โอนไป SCB x8533 นางสาว มัลลิกา สุดใจดี  ','2025-03-30','expense','completed','12:37:00.000000','2025-05-03 20:42:26.841398','import',1,'12:37','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.867195',1,15);
INSERT INTO "transaction" VALUES(110,37589.999999999999999,'รับโอนจาก SCB x0562 นางสาว ธัญวรัตน์ รุ่','2025-04-02','income','completed','18:19:00.000000','2025-05-03 20:42:26.841529','import',1,'18:19','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.867206',1,1);
INSERT INTO "transaction" VALUES(111,6989.9999999999999997,'กสิกรไทย (KBANK) /X129917               ','2025-04-04','income','completed','16:28:00.000000','2025-05-03 20:42:26.841668','import',1,'16:28','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.867215',1,1);
INSERT INTO "transaction" VALUES(112,6989.9999999999999997,'Transfer from SCB x3287 นาย อัครเดช อิทธ','2025-04-05','income','completed','17:08:00.000000','2025-05-03 20:42:26.841793','import',1,'17:08','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.867223',1,1);
INSERT INTO "transaction" VALUES(113,10318.049999999999271,'CREDIT CARD DIVISION(EDC)               ','2025-04-06','income','completed','02:31:00.000000','2025-05-03 20:42:26.841902','import',1,'02:31','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.867233',1,1);
INSERT INTO "transaction" VALUES(114,9855.2499999999999998,'CREDIT CARD DIVISION(EDC)               ','2025-04-07','income','completed','02:03:00.000000','2025-05-03 20:42:26.842012','import',1,'02:03','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.867244',1,1);
INSERT INTO "transaction" VALUES(115,6290.9999999999999999,'กสิกรไทย (KBANK) /X751885               ','2025-04-07','income','completed','20:35:00.000000','2025-05-03 20:42:26.842125','import',1,'20:35','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.867253',1,1);
INSERT INTO "transaction" VALUES(116,27392.0,'โอนไป KBANK x0739 บจก. เบทเทอร์ ช้อยส์ . (ค่าน้ำดื่ม CodeLab 400P.)','2025-04-08','expense','completed','12:58:00.000000','2025-05-03 20:42:26.842260','import',1,'12:58','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.867264',1,9);
INSERT INTO "transaction" VALUES(117,5.0,'ค่าธรรมเนียมโอนไป KBANK x0739 บจก. เบทเท (ค่าน้ำดื่ม CodeLab 400P.)','2025-04-08','expense','completed','12:58:00.000000','2025-05-03 20:42:26.842389','import',1,'12:58','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.867275',1,9);
INSERT INTO "transaction" VALUES(118,1000.0,'โอนไป SCB x0298 นาย ณัฐวัฒน์ โตบัว       (ค่าสติ๊กเกอร์ติดหน้าประตู)','2025-04-08','expense','completed','12:58:00.000000','2025-05-03 20:42:26.842494','import',1,'12:58','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.867285',1,8);
INSERT INTO "transaction" VALUES(119,13096.799999999999272,'โอนไป SCB x0257 บริษัท ทิงค์เน็ต จำกัด  ','2025-04-09','expense','completed','16:32:00.000000','2025-05-03 20:42:26.842636','import',1,'16:32','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.867294',1,16);
INSERT INTO "transaction" VALUES(120,6989.9999999999999997,'กรุงศรีอยุธยา (BAY) /X582690            ','2025-04-10','income','completed','10:36:00.000000','2025-05-03 20:42:26.842767','import',1,'10:36','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.867302',1,1);
INSERT INTO "transaction" VALUES(121,15.0,'จ่ายบิล REVENUE DEPARTMENT (กรมสร        (ค่าภงด 3&53-CodeLab-(03/68))','2025-04-17','expense','completed','13:01:00.000000','2025-05-03 20:42:26.842901','import',1,'13:01','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.867310',1,16);
INSERT INTO "transaction" VALUES(122,4337.0799999999999274,'จ่ายบิล REVENUE DEPARTMENT (กรมสร        (ค่าภงด 3&53-CodeLab-(03/68))','2025-04-17','expense','completed','13:01:00.000000','2025-05-03 20:42:26.843024','import',1,'13:01','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.867319',1,16);
INSERT INTO "transaction" VALUES(123,5.0,'ค่าธรรมเนียมโอนไป KBANK x2362 น.ส. อริศร (ค่าบริการทำบัญชี-CodeLab (03/68))','2025-04-17','expense','completed','13:04:00.000000','2025-05-03 20:42:26.843147','import',1,'13:04','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.867327',1,16);
INSERT INTO "transaction" VALUES(124,2910.0,'โอนไป KBANK x2362 น.ส. อริศรา หล้าที     (ค่าบริการทำบัญชี-CodeLab (03/68))','2025-04-17','expense','completed','13:04:00.000000','2025-05-03 20:42:26.843263','import',1,'13:04','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.867339',1,37);
INSERT INTO "transaction" VALUES(125,5.0,'ค่าธรรมเนียมโอนไป KBANK x5793 นาย จักพรร','2025-04-19','expense','completed','11:29:00.000000','2025-05-03 20:42:26.843396','import',1,'11:29','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.867347',1,18);
INSERT INTO "transaction" VALUES(126,191.99999999999999999,'โอนไป KBANK x5793 นาย จักพรรณ ศรีรอดบาง ','2025-04-19','expense','completed','11:29:00.000000','2025-05-03 20:42:26.843516','import',1,'11:29','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.867357',1,15);
INSERT INTO "transaction" VALUES(127,784.00000000000000001,'โอนไป SCB x8533 นางสาว มัลลิกา สุดใจดี  ','2025-04-20','expense','completed','09:49:00.000000','2025-05-03 20:42:26.843635','import',1,'09:49','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.867368',1,15);
INSERT INTO "transaction" VALUES(128,5.0,'ค่าธรรมเนียมโอนไป KBANK x4555 บจก. ทีพีไ (ค่าขนส่งสินค้า TPI)','2025-04-20','expense','completed','09:50:00.000000','2025-05-03 20:42:26.843764','import',1,'09:50','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.867379',1,15);
INSERT INTO "transaction" VALUES(129,519.99999999999999998,'โอนไป KBANK x4555 บจก. ทีพีไอ.อิมปอร์ต-เ (ค่าขนส่งสินค้า TPI)','2025-04-20','expense','completed','09:50:00.000000','2025-05-03 20:42:26.843916','import',1,'09:50','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.867390',1,11);
INSERT INTO "transaction" VALUES(130,14364.999999999999999,'กรุงศรีอยุธยา (BAY) /X000999            ','2025-04-20','income','completed','17:48:00.000000','2025-05-03 20:42:26.844048','import',1,'17:48','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.867401',1,1);
INSERT INTO "transaction" VALUES(131,308.99999999999999999,'โอนไป SCB x8533 นางสาว มัลลิกา สุดใจดี  ','2025-04-20','expense','completed','21:34:00.000000','2025-05-03 20:42:26.844184','import',1,'21:34','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.867410',1,15);
INSERT INTO "transaction" VALUES(132,1439.0,'โอนไป SCB x8533 นางสาว มัลลิกา สุดใจดี  ','2025-04-22','expense','completed','05:28:00.000000','2025-05-03 20:42:26.844312','import',1,'05:28','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.867418',1,15);
INSERT INTO "transaction" VALUES(133,2505.0000000000000001,'โอนไป SCB x0562 นางสาว ธัญวรัตน์ รุ่งโรจ (ค่าพัดลมตั้งพื้น 2247และเครื่องเขียน258)','2025-04-23','expense','completed','12:26:00.000000','2025-05-03 20:42:26.844444','import',1,'12:26','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.867426',1,15);
INSERT INTO "transaction" VALUES(134,12500.0,'โอนไป KBANK x5727 น.ส. เพ็ญศรี เที่ยงสุข (ค่าผลิตงานเคาท์เตอร์ CodeLab (งวดแรก 50))','2025-04-24','expense','completed','11:56:00.000000','2025-05-03 20:42:26.844574','import',1,'11:56','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.867434',1,8);
INSERT INTO "transaction" VALUES(135,5.0,'ค่าธรรมเนียมโอนไป KBANK x5727 น.ส. เพ็ญศ','2025-04-24','expense','completed','11:56:00.000000','2025-05-03 20:42:26.844698','import',1,'11:56','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.867443',1,8);
INSERT INTO "transaction" VALUES(136,1544.1199999999998908,'โอนไป SCB x0562 นางสาว ธัญวรัตน์ รุ่งโรจ (ค่าอินเตอร์เน็ต CodeLab)','2025-04-24','expense','completed','19:53:00.000000','2025-05-03 20:42:26.844808','import',1,'19:53','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.867452',1,10);
INSERT INTO "transaction" VALUES(137,25999.999999999999999,'โอนไป SCB x5806 บริษัท แอมป์สตาร์ค จำกัด (ค่าบริการสถานที่-(02/68) (18-28/2/68)10ว)','2025-04-24','expense','completed','19:53:00.000000','2025-05-03 20:42:26.844929','import',1,'19:53','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.867460',1,10);
INSERT INTO "transaction" VALUES(138,72800.000000000000001,'โอนไป SCB x5806 บริษัท แอมป์สตาร์ค จำกัด (ค่าบริการสถานที่-(03/68))','2025-04-24','expense','completed','19:54:00.000000','2025-05-03 20:42:26.845031','import',1,'19:54','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.867469',1,10);
INSERT INTO "transaction" VALUES(139,1370.0,'โอนไป SCB x8533 นางสาว มัลลิกา สุดใจดี  ','2025-04-27','expense','completed','12:28:00.000000','2025-05-03 20:42:26.845146','import',1,'12:28','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.867479',1,15);
INSERT INTO "transaction" VALUES(140,784.00000000000000001,'กสิกรไทย (KBANK) /X085170               ','2025-04-27','income','completed','12:35:00.000000','2025-05-03 20:42:26.845270','import',1,'12:35','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.867489',1,1);
INSERT INTO "transaction" VALUES(141,15491.690000000000508,'CREDIT CARD DIVISION(EDC)               ','2025-04-28','income','completed','01:45:00.000000','2025-05-03 20:42:26.845501','import',1,'01:45','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.867494',1,1);
INSERT INTO "transaction" VALUES(142,6290.9999999999999999,'กสิกรไทย (KBANK) /X751885               ','2025-04-28','income','completed','09:11:00.000000','2025-05-03 20:42:26.845632','import',1,'09:11','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.867504',1,1);
INSERT INTO "transaction" VALUES(143,2005.0000000000000001,'โอนไป SCB x8533 นางสาว มัลลิกา สุดใจดี  ','2025-04-28','expense','completed','12:22:00.000000','2025-05-03 20:42:26.845739','import',1,'12:22','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.867513',1,15);
INSERT INTO "transaction" VALUES(144,9699.9999999999999998,'โอนไป SCB x1318 นางสาว แพรวรุ่ง ประทีป   (ค่าจ้างคุณแพรว (04/68))','2025-04-28','expense','completed','19:19:00.000000','2025-05-03 20:42:26.845850','import',1,'19:19','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.867523',1,12);
INSERT INTO "transaction" VALUES(145,55076.599999999998544,'IBFT 270422003412 c912c92d31414472bed863','2025-04-28','expense','completed','19:19:00.000000','2025-05-03 20:42:26.845964','import',1,'19:19','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.867530',1,12);
INSERT INTO "transaction" VALUES(146,1940.0,'โอนไป KBANK x2562 นาย ดินธนารัฐ จันทร์แส','2025-04-29','expense','completed','15:15:00.000000','2025-05-03 20:42:26.846066','import',1,'15:15','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.867539',1,12);
INSERT INTO "transaction" VALUES(147,5.0,'ค่าธรรมเนียมโอนไป KBANK x2562 นาย ดินธนา','2025-04-29','expense','completed','15:15:00.000000','2025-05-03 20:42:26.846173','import',1,'15:15','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.867546',1,12);
INSERT INTO "transaction" VALUES(148,5.0,'ค่าธรรมเนียมโอนไป KBANK x7834 นาย ภิรภัท','2025-04-29','expense','completed','15:16:00.000000','2025-05-03 20:42:26.846275','import',1,'15:16','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.867555',1,12);
INSERT INTO "transaction" VALUES(149,500.0,'โอนไป KBANK x7834 นาย ภิรภัทร กล่อมจิต  ','2025-04-29','expense','completed','15:16:00.000000','2025-05-03 20:42:26.846382','import',1,'15:16','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.867560',1,12);
INSERT INTO "transaction" VALUES(150,20845.299999999999272,'โอนไป KBANK x7289 นาย อภิชาติ แสนบุญเรือ (ค่าติดตั้งงานบันได&อ่างล้างหน้า&ประตู-CL)','2025-04-29','expense','completed','20:22:00.000000','2025-05-03 20:42:26.846504','import',1,'20:22','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.867566',1,8);
INSERT INTO "transaction" VALUES(151,5.0,'ค่าธรรมเนียมโอนไป KBANK x7289 นาย อภิชาต','2025-04-29','expense','completed','20:22:00.000000','2025-05-03 20:42:26.846644','import',1,'20:22','722e1c15-3acc-4f93-8871-e928a3e546a5','2025-05-03 20:42:26.867574',1,8);
INSERT INTO "transaction" VALUES(152,599998.99999999999999,'เงินตั้งต้นลงทุน','2025-02-18','income','completed','13:04:00.000000','2025-05-03 20:44:31.003585','manual',1,NULL,NULL,'2025-05-03 20:44:31.005459',1,38);
INSERT INTO "transaction" VALUES(153,2742.699999999999818,'รายรับเบื้องต้น ให้ เงินตั้งต้น ตรงกัน','2025-02-20','income','completed','13:04:00.000000','2025-05-03 20:46:13.243932','manual',1,NULL,NULL,'2025-05-03 20:46:13.246421',1,38);
COMMIT;