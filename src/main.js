// 常量定义
const DAYS_PER_WEEK = 7;
const TOTAL_SECTIONS = 8;

// DOM 元素引用
const form = document.getElementById('course-form');
const courseNameInput = document.getElementById('course-name');
const teacherInput = document.getElementById('teacher');
const locationInput = document.getElementById('location');
const weekdaySelect = document.getElementById('weekday');
const sectionSelect = document.getElementById('section');
const colorInput = document.getElementById('color');
const clearBtn = document.getElementById('clear-btn');
const scheduleBody = document.getElementById('schedule-body');

// localStorage 存储键名（关闭页面后仍保留）
const STORAGE_KEY = 'course_schedule_data_v1';

/**
 * 从 localStorage 读取课程数据
 */
function loadCoursesFromStorage() {
    try {
        const raw = localStorage.getItem(STORAGE_KEY);
        if (!raw) return [];
        const parsed = JSON.parse(raw);
        if (Array.isArray(parsed)) return parsed;
        return [];
    } catch (e) {
        console.warn('读取本地课程数据失败：', e);
        return [];
    }
}

/**
 * 将当前 courses 保存到 localStorage
 */
function saveCoursesToStorage() {
    try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(courses));
    } catch (e) {
        console.warn('保存课程数据失败（可能 localStorage 不可用或容量不足）：', e);
    }
}

// 课程数据（启动时从本地恢复；后续操作自动同步保存）
let courses = loadCoursesFromStorage();

// ====== 教务处课表解析相关元素 ======
const importTextInput = document.getElementById('import-text');
const parseBtn = document.getElementById('parse-btn');
const clearImportBtn = document.getElementById('clear-import-btn');
const demoBtn = document.getElementById('demo-btn');
const importResult = document.getElementById('import-result');

// 预设课程颜色池（自动分配，避免用户手动选色）
const COLOR_PALETTE = [
    '#4a90e2', '#e74c3c', '#27ae60', '#f39c12',
    '#9b59b6', '#16a085', '#e67e22', '#3498db',
    '#d35400', '#8e44ad', '#2c3e50', '#c0392b',
    '#1abc9c', '#f1c40f', '#34495e'
];

/**
 * 颜色哈希：相同的课程名分配相同的颜色
 */
function colorForCourse(name) {
    let hash = 0;
    for (let i = 0; i < name.length; i++) {
        hash = (hash * 31 + name.charCodeAt(i)) >>> 0;
    }
    return COLOR_PALETTE[hash % COLOR_PALETTE.length];
}

/**
 * 解析 "星期一" / "周一" / "周1" / "1" → 数字 1-7
 */
function parseWeekday(str) {
    if (!str) return null;
    const s = trim(str);
    const m = s.match(/周?\s*([一二三四五六日天1-7])/);
    if (!m) return null;
    const map = { '一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '日': 7, '天': 7, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7 };
    return map[m[1]] || null;
}

/**
 * 解析 "第1-2节" / "第1,2节" / "1-2节" → 节次数组 [1, 2]
 * 同时支持 "第3节" 单节形式
 */
function parseSections(str) {
    if (!str) return null;
    const s = trim(str);
    const results = [];
    // 匹配 "1-2" 或 "1,2" 或 "1、2" 或 单个数字
    const rangeRegex = /(\d+)\s*[-–~～至到]\s*(\d+)/g;
    let match;
    while ((match = rangeRegex.exec(s)) !== null) {
        const start = parseInt(match[1], 10);
        const end = parseInt(match[2], 10);
        if (start >= 1 && end <= 12 && start <= end) {
            for (let i = start; i <= end; i++) results.push(i);
        }
    }
    const singleRegex = /(?:^|[^\d])(\d+)(?=[^\d节]|$|节)/g;
    while ((match = singleRegex.exec(s)) !== null) {
        const n = parseInt(match[1], 10);
        if (n >= 1 && n <= 12 && !results.includes(n)) {
            results.push(n);
        }
    }
    // 如果 range 没匹配到，尝试找所有数字作为节次
    if (results.length === 0) {
        const nums = s.match(/\d+/g);
        if (nums) {
            nums.forEach(n => {
                const num = parseInt(n, 10);
                if (num >= 1 && num <= 12) results.push(num);
            });
        }
    }
    // 去重并排序
    return [...new Set(results)].sort((a, b) => a - b);
}

/**
 * 从粘贴的一大段文本中，逐行解析课程
 * 支持多种常见格式：
 *   - 制表符/空格分隔：课程名\t教师\t地点\t星期\t节次
 *   - HTML 表格（<table>...</table>）
 *   - 逗号/分号分隔
 */
function parseCourseText(rawText) {
    const found = [];
    if (!rawText) return found;

    // ====== 第 1 步：如果包含 HTML，先尝试解析 HTML 表格 ======
    if (/<table/i.test(rawText)) {
        const htmlCourses = parseHtmlTable(rawText);
        if (htmlCourses.length > 0) return htmlCourses;
    }

    // ====== 第 2 步：按行解析纯文本 ======
    const lines = rawText.split(/\r?\n/).map(l => trim(l)).filter(l => l.length > 0);

    for (const line of lines) {
        // 跳过标题行/表头行
        if (/^(课程|课名|名称|教师|老师|地点|教室|星期|时间|节次|周次|周|备注)/.test(line)) continue;
        if (/课程.*教师|教师.*地点|地点.*星期|星期.*节次/.test(line) && line.length < 40) continue;

        // 按分隔符切分（tab、多空格、逗号、分号、竖线、中文顿号/逗号/分号）
        const parts = line.split(/[\t,，;；|｜、]+|\s{2,}/).map(p => trim(p)).filter(p => p.length > 0);

        if (parts.length >= 4) {
            // 多字段行：尝试识别课程名、教师、地点、星期、节次
            let courseName = '', teacher = '', location = '', weekday = null, sections = [];
            for (const p of parts) {
                if (weekday === null && parseWeekday(p)) { weekday = parseWeekday(p); continue; }
                if (sections.length === 0 && /节|第\d|\d[-–~～至到]\d/.test(p)) {
                    const secs = parseSections(p);
                    if (secs.length > 0) { sections = secs; continue; }
                }
                if (!courseName && teacher === '' && location === '' && weekday === null && sections.length === 0) {
                    courseName = p; continue;
                }
                if (courseName && !teacher) { teacher = p; continue; }
                if (courseName && teacher && !location) { location = p; continue; }
                if (!location) { location = p; continue; }
            }
            if (courseName && weekday !== null && sections.length > 0) {
                sections.forEach(sec => {
                    found.push({
                        name: courseName, teacher: teacher || '未知教师',
                        location: location || '未知地点', weekday, section: sec,
                        color: colorForCourse(courseName)
                    });
                });
            }
            continue;
        }

        // 单行格式：如 "高等数学 张老师 教学楼A101 星期一 第1-2节"
        const weekdayMatch = line.match(/周?\s*[一二三四五六日天]/) || line.match(/周?\s*[1-7]/);
        const sectionMatch = line.match(/(?:第)?\s*(\d+\s*[-–~～至到,，]*\s*\d*\s*节?|\d+\s*节)/);
        if (weekdayMatch && sectionMatch) {
            const wd = parseWeekday(line);
            const secs = parseSections(line);
            if (wd && secs.length > 0) {
                // 去掉星期和节次部分，剩余内容按顺序：课程名、教师、地点
                let remaining = line
                    .replace(/周?\s*[一二三四五六日天1-7]\S*/g, ' ')
                    .replace(/第?\s*\d+\s*[-–~～至到,，]*\s*\d*\s*节?/g, ' ')
                    .replace(/\s+/g, ' ').trim();
                const tokens = remaining.split(/[\t,，;；|｜、]|\s+/).filter(t => t.length > 0);
                const courseName = tokens[0] || '课程';
                const teacher = tokens[1] || '未知教师';
                const location = tokens[2] || '未知地点';
                secs.forEach(sec => {
                    found.push({
                        name: courseName, teacher, location,
                        weekday: wd, section: sec, color: colorForCourse(courseName)
                    });
                });
            }
        }
    }
    return found;
}

/**
 * 解析 HTML 表格形式的课表（从教务处复制粘贴可能带 HTML）
 */
function parseHtmlTable(html) {
    const found = [];
    try {
        const parser = new DOMParser();
        const doc = parser.parseFromString('<div>' + html + '</div>', 'text/html');
        const tables = doc.querySelectorAll('table');
        tables.forEach(table => {
            const rows = table.querySelectorAll('tr');
            const headerCells = [];
            // 第一行：识别星期表头
            if (rows.length > 0) {
                const firstRow = rows[0].querySelectorAll('th,td');
                firstRow.forEach(cell => {
                    const txt = cell.textContent.trim();
                    if (parseWeekday(txt)) headerCells.push(parseWeekday(txt));
                    else headerCells.push(null);
                });
            }
            // 后续行：第一列是节次，其余是课程
            for (let r = 1; r < rows.length; r++) {
                const cells = rows[r].querySelectorAll('td,th');
                if (cells.length < 2) continue;
                const firstCellText = cells[0].textContent.trim();
                const sectionNums = parseSections(firstCellText);
                if (sectionNums.length === 0) continue;
                for (let c = 1; c < cells.length && c < headerCells.length; c++) {
                    const wd = headerCells[c];
                    if (!wd) continue;
                    const content = cells[c].textContent.trim();
                    if (!content || content.length < 2) continue;
                    // 单元格内可能包含多行：课程名、教师、地点
                    const lines = content.split(/\n+/).map(s => trim(s)).filter(s => s.length > 0);
                    if (lines.length >= 1) {
                        const courseName = lines[0];
                        const teacher = lines[1] || '未知教师';
                        const location = lines[2] || '未知地点';
                        sectionNums.forEach(sec => {
                            found.push({
                                name: courseName, teacher, location,
                                weekday: wd, section: sec, color: colorForCourse(courseName)
                            });
                        });
                    }
                }
            }
        });
    } catch (e) {
        console.warn('HTML 解析失败，改用纯文本解析', e);
    }
    return found;
}

/**
 * 去重：已存在时间冲突的课程不再添加
 */
function mergeCourses(newCourses) {
    const added = [];
    const skipped = [];
    newCourses.forEach(c => {
        const conflict = courses.some(
            ex => ex.weekday === c.weekday && ex.section === c.section
        );
        if (conflict) { skipped.push(c); return; }
        courses.push(c);
        added.push(c);
    });
    return { added, skipped };
}

/**
 * 显示解析结果提示
 */
function showImportResult(type, message, items) {
    importResult.className = `import-result show ${type}`;
    let html = `<div><strong>${message}</strong></div>`;
    if (items && items.length > 0) {
        html += `<ul class="parsed-list">`;
        items.slice(0, 10).forEach(c => {
            html += `<li>• ${escapeHtml(c.name)}（${escapeHtml(c.teacher)}，${escapeHtml(c.location)}）· 周${c.weekday} 第${c.section}节</li>`;
        });
        if (items.length > 10) html += `<li>... 等 ${items.length} 条</li>`;
        html += `</ul>`;
    }
    importResult.innerHTML = html;
}

/**
 * 示例数据（演示用）
 */
function getDemoData() {
    return `高等数学\t张教授\t教学楼A-101\t星期一\t第1-2节
线性代数\t李老师\t教学楼B-203\t星期二\t第3-4节
大学英语\t王老师\t外语楼-305\t星期三\t第5-6节
程序设计\t陈教授\t信息楼-402\t星期四\t第1-2节
体育（篮球）\t刘教练\t体育馆\t星期五\t第7-8节
思想道德\t赵老师\t文一楼-108\t星期一\t第3-4节
数据结构\t周教授\t信息楼-301\t星期三\t第1-2节`;
}

/**
 * 初始化空表格：8 行节次 × 7 列星期
 */
function initTable() {
    scheduleBody.innerHTML = '';
    for (let section = 1; section <= TOTAL_SECTIONS; section++) {
        const tr = document.createElement('tr');
        // 第一列：节次
        const sectionTd = document.createElement('td');
        sectionTd.textContent = `第 ${section} 节`;
        tr.appendChild(sectionTd);
        // 其余 7 列：星期一到星期日
        for (let day = 1; day <= DAYS_PER_WEEK; day++) {
            const td = document.createElement('td');
            td.dataset.weekday = day;
            td.dataset.section = section;
            td.innerHTML = '<span class="empty-cell">—</span>';
            tr.appendChild(td);
        }
        scheduleBody.appendChild(tr);
    }
}

/**
 * 判断是否为移动端（宽度 <= 768px）
 */
function isMobile() {
    return window.innerWidth <= 768;
}

/**
 * 根据当前 courses 数组渲染课程到表格
 */
function renderCourses() {
    initTable();
    const dayNames = ['', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日'];
    const shortDayNames = ['', '一', '二', '三', '四', '五', '六', '日'];
    const mobile = isMobile();
    courses.forEach((course) => {
        const targetCell = document.querySelector(
            `td[data-weekday="${course.weekday}"][data-section="${course.section}"]`
        );
        if (targetCell) {
            // 移动端：只显示课程名 + 地点，空间更紧凑；桌面端：显示完整信息
            if (mobile) {
                targetCell.innerHTML = `
                    <div class="course-cell" style="background-color: ${course.color};">
                        <div class="course-name">${escapeHtml(course.name)}</div>
                        <div class="course-info">${escapeHtml(course.location)}</div>
                        <div class="course-info">${shortDayNames[course.weekday]}·${course.section}节</div>
                    </div>
                `;
            } else {
                targetCell.innerHTML = `
                    <div class="course-cell" style="background-color: ${course.color};">
                        <div class="course-name">${escapeHtml(course.name)}</div>
                        <div class="course-info">${escapeHtml(course.teacher)}</div>
                        <div class="course-info">${escapeHtml(course.location)}</div>
                        <div class="course-info">${dayNames[course.weekday]} · 第${course.section}节</div>
                    </div>
                `;
            }
        }
    });
}

/**
 * HTML 转义，防止 XSS
 */
function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

/**
 * 去除字符串两端空白
 */
function trim(str) {
    return str ? str.trim() : '';
}

/**
 * 表单提交：添加课程
 */
form.addEventListener('submit', function (e) {
    e.preventDefault();

    const name = trim(courseNameInput.value);
    const teacher = trim(teacherInput.value);
    const location = trim(locationInput.value);
    const weekday = weekdaySelect.value;
    const section = sectionSelect.value;
    const color = colorInput.value;

    // 非空校验
    if (!name) {
        alert('请输入课程名称！');
        courseNameInput.focus();
        return;
    }
    if (!teacher) {
        alert('请输入教师姓名！');
        teacherInput.focus();
        return;
    }
    if (!location) {
        alert('请输入上课地点！');
        locationInput.focus();
        return;
    }
    if (!weekday) {
        alert('请选择星期！');
        weekdaySelect.focus();
        return;
    }
    if (!section) {
        alert('请选择节次！');
        sectionSelect.focus();
        return;
    }

    // 时间冲突校验
    const conflict = courses.some(
        (c) => c.weekday === Number(weekday) && c.section === Number(section)
    );
    if (conflict) {
        const dayNames = ['', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日'];
        alert(`冲突：${dayNames[weekday]} 第 ${section} 节已有课程，请更换时间！`);
        return;
    }

    // 添加课程
    courses.push({
        name,
        teacher,
        location,
        weekday: Number(weekday),
        section: Number(section),
        color,
    });

    // 持久化到本地 + 重新渲染
    saveCoursesToStorage();
    renderCourses();

    // 重置表单（保留颜色）
    form.reset();
    colorInput.value = color;
    courseNameInput.focus();
});

/**
 * 清空按钮：清除所有课程
 */
clearBtn.addEventListener('click', function () {
    if (courses.length === 0) {
        alert('当前没有课程可清空~');
        return;
    }
    if (confirm('确定要清空所有课程吗？此操作不可撤销。')) {
        courses = [];
        saveCoursesToStorage();
        renderCourses();
    }
});

/**
 * 页面加载后初始化：自动渲染之前保存的课程
 */
document.addEventListener('DOMContentLoaded', function () {
    initTable();
    renderCourses();
    if (courses.length > 0) {
        console.log(`💾 已从本地恢复 ${courses.length} 门课程`);
    }
});

/**
 * 窗口大小变化时重新渲染（横竖屏切换）
 */
let resizeTimer = null;
window.addEventListener('resize', function () {
    if (resizeTimer) clearTimeout(resizeTimer);
    resizeTimer = setTimeout(function () {
        renderCourses();
    }, 200);
});

// ============================================================
//      ⬇️  教务处课表导入 —— 按钮事件（缺失部分已补上）
// ============================================================

/**
 * 🔍 解析并导入
 */
parseBtn.addEventListener('click', function () {
    const rawText = importTextInput.value;
    if (!trim(rawText)) {
        showImportResult('error', '❌ 请先在上面的文本框中粘贴教务处课表内容！');
        return;
    }
    const parsed = parseCourseText(rawText);
    if (parsed.length === 0) {
        showImportResult('warning', '⚠️ 没有解析到任何课程。请检查粘贴的内容，或点击"📝 示例数据"测试。');
        return;
    }
    const { added, skipped } = mergeCourses(parsed);
    saveCoursesToStorage();
    renderCourses();
    if (added.length === 0) {
        showImportResult('warning', `⚠️ 解析到 ${parsed.length} 门课程，但全部与已有课程时间冲突，未添加。`);
    } else if (skipped.length > 0) {
        showImportResult('success', `✅ 成功导入 ${added.length} 门课程（跳过 ${skipped.length} 门冲突课程`, added);
    } else {
        showImportResult('success', `✅ 成功导入 ${added.length} 门课程！`, added);
    }
});

/**
 * 清空输入文本 + 结果提示
 */
clearImportBtn.addEventListener('click', function () {
    importTextInput.value = '';
    importResult.className = 'import-result';
    importResult.innerHTML = '';
    importTextInput.focus();
});

/**
 * 📝 载入示例数据（方便测试）
 */
demoBtn.addEventListener('click', function () {
    importTextInput.value = getDemoData();
    showImportResult('success', '📄 已载入示例数据，点击"🔍 解析并导入"试试！');
});

// ============================================================
//      ✏️  单节课编辑 / 删除功能
// ============================================================

// ------ 弹窗相关 DOM ------
const editModal = document.getElementById('edit-modal');
const editNameInput = document.getElementById('edit-name');
const editTeacherInput = document.getElementById('edit-teacher');
const editLocationInput = document.getElementById('edit-location');
const editWeekdaySelect = document.getElementById('edit-weekday');
const editSectionSelect = document.getElementById('edit-section');
const editColorInput = document.getElementById('edit-color');
const editSaveBtn = document.getElementById('edit-save-btn');
const editDeleteBtn = document.getElementById('edit-delete-btn');
const editCancelBtn = document.getElementById('edit-cancel-btn');

// 当前正在编辑的课程索引（-1 表示未编辑任何课程）
let editingIndex = -1;

/**
 * 根据 weekday + section 在 courses 数组中查找对应课程的索引
 */
function findCourseIndex(weekday, section) {
    return courses.findIndex(
        (c) => c.weekday === Number(weekday) && c.section === Number(section)
    );
}

/**
 * 打开编辑弹窗
 */
function openEditModal(weekday, section) {
    const idx = findCourseIndex(weekday, section);
    if (idx === -1) return;
    const c = courses[idx];
    editingIndex = idx;

    // 填入当前课程信息
    editNameInput.value = c.name;
    editTeacherInput.value = c.teacher;
    editLocationInput.value = c.location;
    editWeekdaySelect.value = String(c.weekday);
    editSectionSelect.value = String(c.section);
    editColorInput.value = c.color;

    editModal.classList.add('show');
    editNameInput.focus();
    editNameInput.select();
}

/**
 * 关闭编辑弹窗
 */
function closeEditModal() {
    editModal.classList.remove('show');
    editingIndex = -1;
}

/**
 * 保存当前编辑：更新 courses 数组 → 保存 → 重绘
 */
function saveEdit() {
    if (editingIndex === -1) return;

    const name = trim(editNameInput.value);
    const teacher = trim(editTeacherInput.value);
    const location = trim(editLocationInput.value);
    const weekday = Number(editWeekdaySelect.value);
    const section = Number(editSectionSelect.value);
    const color = editColorInput.value;

    // 非空校验
    if (!name) { alert('请输入课程名称！'); editNameInput.focus(); return; }
    if (!teacher) { alert('请输入教师姓名！'); editTeacherInput.focus(); return; }
    if (!location) { alert('请输入上课地点！'); editLocationInput.focus(); return; }

    // 时间冲突校验：如果星期/节次变了，要检查新位置是否被占
    const conflictIdx = findCourseIndex(weekday, section);
    if (conflictIdx !== -1 && conflictIdx !== editingIndex) {
        const dayNames = ['', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日'];
        alert(`冲突：${dayNames[weekday]} 第 ${section} 节已有其他课程，请更换时间！`);
        return;
    }

    // 更新课程
    courses[editingIndex] = { name, teacher, location, weekday, section, color };
    saveCoursesToStorage();
    renderCourses();
    closeEditModal();
}

/**
 * 删除当前编辑的课程
 */
function deleteEdit() {
    if (editingIndex === -1) return;
    const c = courses[editingIndex];
    if (!confirm(`确定删除课程「${c.name}」（${c.teacher}，${c.location}）？`)) return;
    courses.splice(editingIndex, 1);
    saveCoursesToStorage();
    renderCourses();
    closeEditModal();
}

// ------ 事件绑定 ------

// 事件委托：点击表格中任意课程格子 → 打开编辑弹窗
document.addEventListener('click', function (e) {
    const cell = e.target.closest('.course-cell');
    if (!cell) return;
    const td = cell.closest('td');
    if (!td || !td.dataset.weekday || !td.dataset.section) return;
    openEditModal(td.dataset.weekday, td.dataset.section);
});

// 弹窗内按钮
editSaveBtn.addEventListener('click', saveEdit);
editDeleteBtn.addEventListener('click', deleteEdit);
editCancelBtn.addEventListener('click', closeEditModal);

// 点击遮罩层（弹窗外区域）→ 关闭
editModal.addEventListener('click', function (e) {
    if (e.target === editModal) closeEditModal();
});

// 按 ESC → 关闭弹窗
document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && editModal.classList.contains('show')) {
        closeEditModal();
    }
    // 弹窗打开时按 Enter → 保存（仅当焦点不在多行输入区时）
    if (e.key === 'Enter' && editModal.classList.contains('show')) {
        const tag = (document.activeElement && document.activeElement.tagName) || '';
        if (tag !== 'TEXTAREA') {
            e.preventDefault();
            saveEdit();
        }
    }
});