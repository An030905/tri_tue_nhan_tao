# Chess AI Arcade

Thành viên nhóm :
-Nhữ Trung Hải
-nguyễn Trọng An
-Phạm nguyễn Hưng

## Giới thiệu

Đây là một trò chơi cờ vua sử dụng thư viện Arcade (Python) với nhiều cấp độ AI:

- **Random AI**: Máy chọn nước đi hợp lệ một cách ngẫu nhiên.
- **Minimax AI**: Máy sử dụng thuật toán Minimax (có cắt tỉa Alpha-Beta) để đánh giá và chọn nước đi tốt nhất dựa trên hàm đánh giá bàn cờ.
- **Hybrid AI**: Máy lấy ra N nước đi tốt nhất theo Minimax, sau đó chọn ngẫu nhiên trong số đó. Điều này giúp AI vừa mạnh vừa khó đoán.

## Cách hoạt động của các thuật toán

### 1. Random AI

- Hàm: `random_ai(board, color, move_log=[])`
- Ý tưởng: Lấy tất cả nước đi hợp lệ, nếu có nước ăn quân thì ưu tiên chọn ngẫu nhiên trong số đó, nếu không thì chọn ngẫu nhiên bất kỳ nước đi nào.
- Độ khó: Dễ, dễ bị bắt bài.

### 2. Minimax AI

- Hàm: `minimax_ai(board, color, move_log=[], depth=2)`
- Ý tưởng: Sử dụng thuật toán Minimax với cắt tỉa Alpha-Beta để duyệt các nước đi có thể xảy ra đến một độ sâu nhất định (depth). Mỗi trạng thái bàn cờ được đánh giá bằng hàm `evaluate_board`, dựa trên tổng giá trị các quân cờ.
- Độ khó: Cao hơn, có thể điều chỉnh bằng tham số `depth` (sâu hơn thì mạnh hơn nhưng chậm hơn).

### 3. Hybrid AI

- Hàm: `ai_hybrid(board, color, move_log=[], depth=2, top_n=3)`
- Ý tưởng: Lấy tất cả nước đi hợp lệ, đánh giá điểm số của từng nước đi bằng Minimax (độ sâu nhỏ hơn), sau đó chọn ngẫu nhiên trong N nước đi tốt nhất. Điều này giúp AI vừa mạnh vừa có tính bất ngờ.
- Độ khó: Trung bình đến cao, tuỳ vào tham số `depth` và `top_n`.

## Cách chọn AI

Trong file `main.py`, bạn có thể thay đổi biến `AI_TYPE` trong hàm `on_mouse_press`:

```python
AI_TYPE = "random"  # hoặc "minimax", "hybrid"
```

- `random`: AI dễ nhất
- `minimax`: AI mạnh nhất (có thể điều chỉnh depth)
- `hybrid`: AI vừa mạnh vừa khó đoán

## Tuỳ chỉnh độ khó

- Thay đổi giá trị `depth` trong các hàm AI để tăng/giảm độ khó.
- Với hybrid, thay đổi `top_n` để điều chỉnh mức độ "ngẫu nhiên" của AI.

## Yêu cầu

- Python 3.x
- arcade >= 3.0

## Chạy game

```bash
python main.py
```

## Thư mục

- `engine.py`: Chứa các thuật toán AI và logic cờ vua
- `main.py`: Giao diện và điều khiển game
- `assets/`: Ảnh quân cờ

---
