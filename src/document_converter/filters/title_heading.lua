-- Formats without a title block would silently drop the document title, so
-- keep it as a top-level heading instead.
function Pandoc(doc)
  local title = doc.meta.title
  if title == nil then
    return doc
  end
  local inlines = pandoc.utils.type(title) == "Inlines" and title
    or pandoc.Inlines { pandoc.Str(pandoc.utils.stringify(title)) }
  table.insert(doc.blocks, 1, pandoc.Header(1, inlines))
  doc.meta.title = nil
  return doc
end
