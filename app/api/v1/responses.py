from fastapi import status

FORBIDDEN = {status.HTTP_403_FORBIDDEN: {"description": "Không đủ quyền"}}
NOT_FOUND = {
    status.HTTP_404_NOT_FOUND: {
        "description": "Không tồn tại, hoặc người dùng không thuộc workspace"
    }
}
