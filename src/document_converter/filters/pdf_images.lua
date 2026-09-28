-- Keep only images the Typst PDF engine can embed. Unsupported images (for
-- example EMF/WMF drawings from Word, or remote URLs) are replaced by their
-- caption so the rest of the document still typesets.
local supported = { png = true, jpg = true, jpeg = true, gif = true, svg = true, webp = true }

function Image(el)
  local src = el.src
  if src:match("^%a[%w+.-]*://") then
    return el.caption
  end
  local ext = src:match("%.([%w]+)$")
  if ext and supported[ext:lower()] then
    return el
  end
  return el.caption
end
