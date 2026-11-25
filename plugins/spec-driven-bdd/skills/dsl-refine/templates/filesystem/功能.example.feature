@module:照片
Feature: 照片檔案儲存

  Background:
    # 預設值：儲存區根目錄為空，沒有任何原始檔、縮圖或暫存檔
    Given 系統處於 "空儲存區"

  Rule: 寫入完成後，原始檔必須在正式路徑

    Example: 寫入照片 P1
      When 寫入照片 "P1"
      Then "P1" 的 "原始檔" 在正式路徑

  Rule: 寫入完成後，暫存區不能留下檔案

    Example: 寫入照片 P1
      When 寫入照片 "P1"
      Then 暫存區沒有任何檔案

  Rule: 回傳的內容雜湊必須是檔案內容的 SHA-256

    Example: 寫入照片 P1
      When 寫入照片 "P1"
      Then 回傳的內容雜湊是 "P1" 內容的 SHA-256

  Rule: 每種支援的格式都必須以原本的副檔名存入

    Scenario Outline: 寫入 <格式> 照片 P1
      When 寫入格式為 "<格式>" 的照片 "P1"
      Then "P1" 的 "原始檔" 在正式路徑

      Examples:
        | 格式 |
        | JPEG |
        | PNG  |
        | HEIC |

  Rule: 刪除照片時，必須移除它的原始檔

    Example: 刪除已存入的照片 P1
      Given 寫入照片 "P1" 與它的縮圖
      When 刪除照片 "P1" 的檔案
      Then "P1" 的 "原始檔" 不在正式路徑

  Rule: 刪除一張照片時，不能動到其他照片的檔案

    Example: 三種格式的照片中刪除 PNG 的 P2
      Given 寫入下列照片與它們的縮圖：
        | 照片 | 格式 |
        | P1   | JPEG |
        | P2   | PNG  |
        | P3   | HEIC |
      When 刪除照片 "P2" 的檔案
      Then 下列檔案仍在正式路徑：
        | 照片 | 檔案種類 |
        | P1   | 原始檔   |
        | P1   | 縮圖     |
        | P3   | 原始檔   |
        | P3   | 縮圖     |
