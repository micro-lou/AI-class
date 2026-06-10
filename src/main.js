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

// 课程数据（内存中存储）
let courses = [];

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
 * 根据当前 courses 数组渲染课程到表格
 */
function renderCourses() {
    initTable();
    const dayNames = ['', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日'];
    courses.forEach((course) => {
        const targetCell = document.querySelector(
            `td[data-weekday="${course.weekday}"][data-section="${course.section}"]`
        );
        if (targetCell) {
            targetCell.innerHTML = `
                <div class="course-cell" style="background-color: ${course.color};">
                    <div class="course-name">${escapeHtml(course.name)}</div>
                    <div class="course-info">${escapeHtml(course.teacher)}</div>
                    <div class="course-info">${escapeHtml(course.location)}</div>
                    <div class="course-info">${dayNames[course.weekday]} · 第${course.section}节</div>
                </div>
            `;
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

    // 重新渲染
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
        renderCourses();
    }
});

/**
 * 页面加载后初始化
 */
document.addEventListener('DOMContentLoaded', function () {
    initTable();
});
