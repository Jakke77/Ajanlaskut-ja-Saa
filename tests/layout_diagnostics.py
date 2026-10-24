"""Read-only geometry evidence attached only to failed layout assertions."""
import json

from PyQt6.QtWidgets import QApplication, QLayout, QWidget


def layout_diagnostics(page, scroll):
    widgets = []
    for item in [page, *page.findChildren(QWidget)]:
        text = item.text() if hasattr(item, 'text') else ''
        widgets.append(dict(type=type(item).__name__, name=item.objectName(),
            minimum=item.minimumSizeHint().width(), hint=item.sizeHint().width(),
            actual=item.width(), policy=item.sizePolicy().horizontalPolicy().name,
            wrap=item.wordWrap() if hasattr(item, 'wordWrap') else None,
            text=text[:80]))
    rows = []
    for item in page.findChildren(QLayout):
        children = []
        for index in range(item.count()):
            child = item.itemAt(index)
            widget = child.widget()
            children.append(dict(type=type(widget).__name__ if widget else 'layout/spacer',
                minimum=child.minimumSize().width(),
                text=widget.text()[:45] if widget and hasattr(widget, 'text') else ''))
        rows.append(dict(type=type(item).__name__, minimum=item.minimumSize().width(),
                         hint=item.sizeHint().width(), children=children))
    record = dict(viewport=scroll.viewport().width(), page=page.width(),
        page_minimum=page.minimumSizeHint().width(), font=QApplication.font().toString(),
        horizontal_overflow=scroll.horizontalScrollBar().maximum(),
        widgets=sorted(widgets, key=lambda row: row['minimum'], reverse=True)[:15],
        rows=sorted(rows, key=lambda row: row['minimum'], reverse=True)[:10])
    return json.dumps(record, ensure_ascii=False, indent=2)
