import re

with open('frontend/src/pages/Inventory.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove MOCK_INVENTORY definition
content = re.sub(r'const MOCK_INVENTORY = \[[\s\S]*?\];\n+', '', content)

# 2. Fix fetchInventory catch block
fetch_replace = r'''    } catch (err) {
      console.warn("Backend not ready, using mock data.", err);
      setItems(MOCK_INVENTORY);
    } finally {'''
fetch_new = r'''    } catch (err) {
      console.error("Failed to fetch inventory", err);
    } finally {'''
content = content.replace(fetch_replace, fetch_new)

# 3. Fix handleSave catch block
save_replace = r'''    } catch\(err\) {
      console.warn\("Using mock update fallback"\);
      if \(modalType === 'add'\) {
        setItems\(\[\.\.\.items, { id: Date\.now\(\), \.\.\.formData }\]\);
      } else if \(modalType === 'edit'\) {
        setItems\(items\.map\(i => i\.id === selectedItem\.id \? { \.\.\.i, \.\.\.formData } : i\)\);
      } else if \(modalType === 'delete'\) {
        setItems\(items\.filter\(i => i\.id !== selectedItem\.id\)\);
      }
      setShowModal\(false\);
    }'''
save_new = r'''    } catch (err) {
      console.error("Failed to save", err);
      alert("حدث خطأ أثناء الحفظ. يرجى المحاولة مرة أخرى.");
    }'''
content = re.sub(save_replace, save_new, content)

with open('frontend/src/pages/Inventory.jsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("Inventory.jsx cleaned of mock fallbacks.")
