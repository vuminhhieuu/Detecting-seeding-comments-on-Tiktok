
# 🕵️ Detecting Seeding Comments on TikTok

> Đồ án môn học **IE403 - Khai thác dữ liệu truyền thông xã hội**  
> Trường: Đại học Công nghệ Thông tin 
> Giảng viên: TS.Nguyễn Văn Kiệt và ThS. Huỳnh Văn Tín  
> Nhóm thực hiện: Nhóm 5

---

## 📌 Giới thiệu

Trong thời đại mạng xã hội phát triển mạnh mẽ, đặc biệt là TikTok, hành vi **seeding** (tạo bình luận giả để quảng bá, thao túng nhận thức) ngày càng phổ biến và tinh vi. Điều này ảnh hưởng đến:
- Trải nghiệm người dùng
- Độ tin cậy của các chỉ số tương tác
- Hiệu quả đánh giá các chiến dịch truyền thông

**Mục tiêu của dự án** là phát hiện các bình luận seeding dựa trên:
- Phân tích nội dung bình luận (text-based)
- Đặc trưng hành vi người dùng (behavioral features)

---

## 🎯 Mục tiêu

- Phát hiện bình luận seeding hoặc spam trên TikTok
- Hỗ trợ TikTokers, doanh nghiệp, nhà quảng cáo đánh giá chất lượng tương tác
- Xây dựng nền tảng hệ thống chống gian lận trên mạng xã hội

---

## 🛠️ Quy trình thực hiện

### 1. Thu thập dữ liệu
- **Nguồn dữ liệu:** Bình luận và người dùng từ TikTok (sử dụng Unoffical TikTok-API)
- **Dữ liệu bao gồm:**
  - Video: `video_id`, `description`, `hashtags`
  - Bình luận: `comment_id`, `comment_text`, `like_count`, `timestamp`, `user_id`
  - Người dùng: `followers`, `comment_count`, `duplicate_ratio`, v.v.
- **Lưu trữ:** CSV, MongoDB hoặc PostgreSQL (Đang cân nhắc)

### 2. Tiền xử lý dữ liệu
- **Văn bản:**
  - Xóa ký tự đặc biệt, link, emoji
  - Chuẩn hoá tiếng Việt (xóa dấu, viết thường)
- **Hành vi người dùng (chưa làm được):**
  - Tính duplicate ratio
  - Cosine similarity giữa các bình luận
  - Tần suất bình luận theo thời gian

### 3. Gán nhãn

Sử dụng 3 LLM(PhoBERT, LLaMA3, Mistral) tự động gán nhãn bình luận dựa trên prompt chuyên biệt. Khoảng 100–200 mẫu được kiểm tra thủ công để đánh giá độ tin cậy. Nhãn cuối cùng hợp nhất bằng weighted voting với trọng số: LLaMA3 (5), Mistral (3), PhoBERT (2). Các mẫu chưa gán nhãn sẽ được xử lý thủ công.


### 4. Xây dựng mô hình
- **Mục tiêu:** Phân loại bình luận là Seeding (`1`) hoặc Không Seeding (`0`)
- **Mô hình sử dụng:**
  - Truyền thống: SVM
  - Deep Learning: LSTM, BiLSTM
  - Transformer: VisoBert, CafeBert, PhoBert, XLM-R, FastText
- **Input:** Văn bản và đặc trưng hành vi
- **Output:** Nhãn nhị phân

### 5. Đánh giá mô hình
- **Chia tập train/dev/test:** 80/10/10
- **Chỉ số đánh giá:** Accuracy, Precision, Recall, F1-score
- **Trực quan hóa:** Confusion Matrix, ROC Curve, WordCloud

### 6. Triển khai ứng dụng
- **Framework backend:** FastAPI
- **Framework frontend:** Vite + React
- **Model**: Hugging face
- **Tính năng chính:**
  - Nhập URL video TikTok
  - Dự đoán % bình luận seeding
  - Hiển thị và tải danh sách bình luận nghi vấn

---

## 🧾 Đầu ra của dự án

| Thành phần       | Mô tả |
|------------------|-------|
| Dataset          | Bình luận TikTok đã gán nhãn seeding / không seeding |
| Mô hình          | Mô hình đã được fine-tune cho việc phát hiện seeding |
| Web App          | Ứng dụng kiểm tra bình luận seeding theo URL |
| Báo cáo          | Tài liệu chi tiết phương pháp và kết quả |

---

## ✅ Kết luận

Dự án mang tính ứng dụng thực tiễn cao, đặc biệt trong bối cảnh mạng xã hội ngày càng bị lạm dụng bởi các chiến dịch seeding. Hệ thống hỗ trợ các bên liên quan:
- Kiểm tra độ trung thực của tương tác
- Phát hiện hành vi gian lận
- Nâng cao độ minh bạch trên các nền tảng UGC (user-generated content)

---

## 📬 Liên hệ 

- Vũ Minh Hiếu - 22520451@gm.uit.edu.vn 
- Ngô Thị Lễ Hội - 22520491@gm.uit.edu.vn
- Nguyễn Tấn Cao Hào - 22520402@gm.uit.edu.vn
- Phạm Võ Gia Huy - 22520572@gm.uit.edu.vn
