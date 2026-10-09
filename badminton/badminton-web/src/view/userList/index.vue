<template>
  <div class="user-management">
    <!-- 顶部搜索和操作栏 -->
    <van-sticky>
      <div class="top-bar">
        <van-search
            v-model="searchKeyword"
            placeholder="搜索选手名"
            shape="round"
            style="border-radius: 25px;border: 1px solid #eaeaea;height: 40px;margin-right: 40px;"
            @search="onSearch"
        />
        <van-button
            type="primary"
            size="small"
            class="add-btn"
            @click="goToCreateUser">
          新增
        </van-button>
      </div>
    </van-sticky>

    <!-- 用户列表 -->
    <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
      <van-list
          v-model="loading"
          :finished="finished"
          finished-text="没有更多了"
          @load="onLoad"
      >
        <van-swipe-cell v-for="user in userList" :key="user.id">
          <van-cell
              style="font-weight: bold;margin-top: 10px;"
              @click="showUserDetail(user)"
          >
            <!-- 使用 default 插槽自定义单元格内容 -->
            <template #default>
              <div>姓名：{{ user.playerName}}</div>
              <div>用户名：{{ user.userName}}</div>
              <div>角色：{{ getRoleTypeText(user.roleType) }}</div>
            </template>
            <template #right-icon>
<!--              <van-tag :type="getRoleTypeTag(user.roleType)">-->
<!--                {{ getRoleTypeText(user.roleType) }}-->
<!--              </van-tag>-->
              <van-button
                  size="small"
                  class="edit"
                  text="编辑"
                  @click.stop="initEditForm(user)"
              />
            </template>
          </van-cell>

          <template #right>
            <van-button
                square
                type="danger"
                text="删除"
                class="delete-button"
                @click.stop="deleteUser(user.id)"
            />
          </template>
        </van-swipe-cell>
      </van-list>
    </van-pull-refresh>

    <!-- 编辑弹窗 -->
    <van-popup v-model="showEdit" class="edit-popup" :style="{ padding:'20px',width:'80%', height: '50%' }">
      <van-nav-bar
          title="修改用户信息"
          left-text="取消"
          right-text="确认"
          @click-left="showEdit = false"
          @click-right="editCurrentUser"
      />
      <van-form class="form-container">
        <van-cell-group inset>
          <van-field
              v-model="editForm.userName"
              label="用户名"
              placeholder="请输入用户名"
              :rules="[{ required: true, message: '请填写用户名' }]"
          />
          <van-field
              v-model="editForm.playerName"
              label="选手名"
              placeholder="请输入选手名"
          />
          <van-field
              v-model="editForm.password"
              type="password"
              label="密码"
              placeholder="留空表示不修改"
          />
          <van-field
              v-model="editForm.gender"
              is-link
              readonly
              label="性别"
              placeholder="选择性别"
              @click="showGenderPicker = true"
          />
          <van-field
              v-model="editForm.currentPoints"
              type="digit"
              label="当前积分"
              placeholder="请输入初始积分"
          />
          <van-field
              v-model="editForm.roleTypeText"
              is-link
              readonly
              label="角色类型"
              placeholder="选择角色类型"
              @click="showRoleTypePicker = true"
          />
        </van-cell-group>
      </van-form>
    </van-popup>

    <!-- 性别选择器 -->
    <van-popup
        v-model="showGenderPicker"
        round
        position="bottom"
        destroy-on-close
    >
      <van-picker
          title="选择性别"
          show-toolbar
          :columns="genderOptions"
          @confirm="onGenderConfirm"
          @cancel="showGenderPicker = false"
      />
    </van-popup>

    <!-- 角色类型选择器 -->
    <van-popup
        v-model="showRoleTypePicker"
        round
        position="bottom"
        destroy-on-close
    >
      <van-picker
          title="选择角色类型"
          show-toolbar
          :columns="roleTypeOptions"
          @confirm="onRoleTypeConfirm"
          @cancel="showRoleTypePicker = false"
      />
    </van-popup>
  </div>
</template>

<script src="./userList.js"></script>

<style scoped>
.user-management {
  padding-bottom: 50px;
  width: 110%;
  margin-left: -5%;
  margin-right: -5%;
}

.top-bar {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  background-color: #fff;
}

.edit {
  border: none;
  color:cornflowerblue;

}
.van-search {
  flex: 1;
  padding: 0;
}

.add-btn {
  margin-left: 10px;
  width: 40px;
  height: 34px;
  border: none;
  background-color: transparent;
  color: black;
  font-weight: bold;
}
.edit-popup {
 border-radius: 20px;
}
.delete-button {
  height: 100%;
}

.form-container {
  padding: 16px;
}

/* 移动端优化 */
@media (max-width: 768px) {
  .van-cell {
    padding: 12px 16px;
  }

  .van-cell__title {
    font-size: 16px;
  }

  .van-cell__label {
    font-size: 14px;
    margin-top: 4px;
  }
}

::v-deep .van-search__content{
  background-color: transparent;
}

::v-deep [class*=van-hairline]::after{
  border: none;
}

::v-deep .van-cell::after{
  border: none;
}

::v-deep .edit-popup input {
  background-color: aliceblue;
  height: 35px;
  text-align: right;
  padding-right: 10px;
}
</style>
