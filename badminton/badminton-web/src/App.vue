<!-- App.vue -->
<template>
  <router-view v-if="$route.meta.noLayout" />
  <div id="app" v-else>
    <div class="layout-container">
      <!-- 移动端菜单按钮 -->
      <van-icon
          v-if="isMobile"
          class="menu-toggle"
          :name="menuCollapsed ? 'wap-nav' : 'cross'"
          @click="toggleMenu"
      />

      <!-- 左侧菜单 -->
      <van-sidebar
          class="menu-sidebar"
          v-model="activeMenu"
          :style="isMobile ? mobileMenuStyle : ''"
      >
        <div class="topTitle">
          <img class="leftIcon" src="@/assets/img/icon.png">
          <div style="margin-top: 20px;font-size: 14px">羽毛球积分系统</div>
        </div>
        <template v-for="(item, index) in store.menuConfig" >
          <van-sidebar-item
              v-if="item.children && item.children.length"
              :key="item.path"
              :title="item.title"
              @click="handleMenuClick(item)"
          >
            <template #title>
              <van-icon :name="item.icon" />
              <span>{{ item.title }}</span>
              <van-icon
                  :name="item.expanded ? 'arrow-down' : 'arrow'"
                  class="menu-arrow"
              />
            </template>

            <div class="submenu" v-show="item.expanded">
              <van-sidebar-item
                  v-for="child in item.children"
                  :key="child.path"
                  :title="child.title"
                  @click="handleSubmenuClick(child)"
              />
            </div>
          </van-sidebar-item>

          <van-sidebar-item
              v-else
              :key="item.path"
              :title="item.title"
              @click="handleMenuClick(item, index)"
          >
            <template #title>
              <van-icon :name="item.icon" />
              <span>{{ item.title }}</span>
            </template>
          </van-sidebar-item>
        </template>
      </van-sidebar>

      <!-- 右侧内容区 -->
      <div class="content-main" :class="{ 'mobile-content': isMobile }">
        <router-view />
      </div>
    </div>
  </div>
</template>

<script src="./init.js"></script>
<style>
body {
  font-size: 16px;
  background-color: #f8f8f8;
  -webkit-font-smoothing: antialiased;
}


.layout-container {
  display: flex;
  height: 100vh;
}
.topTitle{
  color:#fff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  padding-top: 20px;
}
.leftIcon{
  width: 40%;
  height: auto;
}
.menu-sidebar {
  width: 140px;
  height: 100%;
  background-color: #3651B1;
  overflow-y: auto;
  padding-top: 20px;
}

.content-main {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

/* 移动端样式 */
.menu-toggle {
  position: fixed;
  top: 10px;
  left: 10px;
  z-index: 1001;
  font-size: 24px;
}

.mobile-content {
  padding-top: 50px;
}

/* 子菜单样式 */
.submenu {
  padding-left: 20px;
  background-color: #f0f2f5;
}

/* 菜单项样式 */
.van-sidebar-item__content {
  display: flex;
  align-items: center;
  background-color: #3651B1;
}
.van-sidebar-item{
  background-color: #3651B1 !important;
  color: #fff;
  padding: 15px 12px !important;
}
/* 移除滑块 */
.van-sidebar-item--select::before {
  display: none !important;
}
.van-icon {
  margin-right: 8px;
}

.menu-arrow {
  margin-left: auto;
  font-size: 12px;
}
</style>
