# 資料庫遷移：004-photo-tags

## 遷移步驟

1. photos：新增欄位 tag_count（INT NOT NULL DEFAULT 0）。
2. 建立 photo_tags：欄位 photo_id（CHAR(36) NOT NULL）、tag（VARCHAR(32) NOT NULL），主鍵 (photo_id, tag)，外鍵 fk_photo_tags_photo_id 參照 photos.id（ON DELETE CASCADE）。

## 既有資料的處理

- photos 既有的列由預設值填入 tag_count = 0，不需要回填。
- photo_tags 是新的資料表，沒有既有資料。
