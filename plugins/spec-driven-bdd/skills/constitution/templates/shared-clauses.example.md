# 共通條款：欄位命名風格

## C-SH-01 -- 對外欄位一律 camelCase，資料庫欄位一律 snake_case

**強度：MUST**
**作用位置**：
- `specs/truth/contracts/components/schemas/*.yaml › properties`、`specs/truth/contracts/paths/*/*.yaml › *.parameters[*].name`
- `specs/truth/data/*.dbml › Table.*` 的欄位名稱

API 的屬性與參數名稱使用 camelCase；資料表與欄位名稱使用 snake_case。同一個概念在兩邊的名稱必須能互相換算，例如 `albumDate` 對應 `album_date`，不得各自取名。

### Good Example

這個範例兩邊的名稱可以機械式換算，對照時不必另查對應表。

```text
Album.yaml  albumDate
相簿.dbml   albums.album_date
```

### Bad Example

這個範例同一個概念在兩邊用了不同的詞，後端實作時要另外記住 `shotOn` 存在 `album_date`。

```text
Album.yaml  shotOn
相簿.dbml   albums.album_date
```
