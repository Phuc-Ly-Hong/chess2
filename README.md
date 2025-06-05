# Dự án chương trình cờ vua với bot (Chess AI)
## Giới thiệu
Dự án này là một chương trình **cờ vua với AI** được phát triển bằng ngôn ngữ Python. Mục tiêu của chúng tôi là xây dựng một trò chơi cờ vua hoàn chỉnh có thể:
- Cho phép người chơi đối đầu với máy (chế độ chơi với bot),
- Hiển thị giao diện trực quan với bàn cờ và quân cờ,
- Kiểm tra nước đi hợp lệ,
- Và triển khai một **bot AI** sử dụng thuật toán **Minimax với cắt tỉa Alpha-Beta** để đưa ra các nước đi thông minh.

Dự án được thiết kế để hỗ trợ người học lập trình và trí tuệ nhân tạo tiếp cận với cách xây dựng một hệ thống chơi game cơ bản nhưng có tính chiến lược, như cờ vua.
## Tính năng
- [x] Chế độ chơi **Người vs Người** (trên cùng một máy)
- [x] Chế độ chơi **Người vs Máy** với bot AI
## Cài đặt
Dưới đây là hướng dẫn cài đặt để chạy chương trình trên máy tính cá nhân:

### ⚙️ Yêu cầu

- Python 3.8 trở lên
- pip (trình quản lý gói của Python)

### 📦 Cài đặt thư viện cần thiết

Mở terminal hoặc command prompt và chạy:

```bash
pip install pygame numpy
```

## Hướng dẫn cách chơi
Sau khi cài đặt đầy đủ các thư viện, bạn làm theo các bước sau để khởi chạy và chơi trò chơi:

1. **Mở terminal hoặc command prompt**, di chuyển vào thư mục chứa dự án:

    ```bash
    cd duong_dan_toi_thu_muc_du_an
    ```

2. **Khởi động chương trình** bằng lệnh:

    ```bash
    python main.py
    ```

3. **Chọn chế độ chơi** khi giao diện xuất hiện:
    - Click chuột để chọn một trong hai chế độ:
      - 🧑‍🤝‍🧑 Người vs Người
      - 🤖 Người vs Máy
        
![image](https://github.com/user-attachments/assets/fb3b8230-39e2-4977-b1b8-cb64a9afe115)

4. Nếu chọn **Người vs Máy**, bạn sẽ được chọn **màu quân**:
    - Click để chọn chơi quân **Trắng** hoặc **Đen**
    - Bot sẽ chơi bên còn lại
      
![image](https://github.com/user-attachments/assets/811554cd-5fd2-4f72-8ef5-ee4b8b959be3)

5. **Giao diện bàn cờ sẽ hiển thị** sau khi chọn xong:
    - Click chuột vào **quân cờ của bạn**
    - Các **nước đi hợp lệ** sẽ sáng lên
    - Click vào ô đích để di chuyển quân
    - Nếu nước đi không hợp lệ, chương trình sẽ không thực hiện và yêu cầu bạn chọn lại
    - ấn phím u trên bàn phim để có thể undo lại nước đi của mình
   
![image](https://github.com/user-attachments/assets/cf29b582-9335-45f5-b5ec-9e4463ed3c1d)

## Thành viên nhóm
Dự án được thực hiện bởi nhóm sinh viên với các thành viên:
| Họ và Tên             |   MSSV   |
|-----------------------|----------|
| Lý Hồng Phúc          | 20235192 |
| Nguyễn Đình Lâm Phúc  | 20235193 |
| Nguyễn Hoài Nam       | 20235175 |
| Lê Tuấn Minh          | 20235160 | 

## Cấu trúc dự án
```bash
Chess_Test/
├── assets/ # Chứa hình ảnh quân cờ, âm thanh 
├── resource/ # Chứa mã nguồn game: xử lý bàn cờ, bot, giao diện, 
│ ├── main.py # File chính để chạy chương trình
│ ├── Book/ # Cơ sở dữ liệu khai cuộc (opening book)
│ ├── core/ # Xử lý giao diện, hiển thị bàn cờ, logic cờ vua
│ ├── engine/ # Bộ máy AI: Minimax, Alpha-Beta, Evaluation...
│ ├── tool/ # thuật toán sprt để đánh giá bot mạnh hay yếu
│ └── pycache/ # File biên dịch tạm thời của Python
├── stockfish/ # (Tuỳ chọn) tích hợp engine Stockfish để sử dụng so sánh bằng sprt
├── README.md # Hướng dẫn sử dụng và mô tả dự án
```


