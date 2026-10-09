<template>
  <div class="user-add-container">
    <!-- 顶部导航栏 -->
    <van-nav-bar
        title="新增用户"
        left-text="返回"
        left-arrow
        @click-left="onBack"
    />

    <!-- 表单区域 -->
    <van-form @submit="handleSubmit">
      <van-cell-group inset style="font-weight: bold;">
        <van-field
            v-model="formData.userName"
            label="用户名"
            placeholder="请输入用户名"
            :rules="[{ required: true }]"
        />
        <van-field
            v-model="formData.playerName"
            label="选手名"
            placeholder="请输入选手名"
        />
        <van-field
            v-model="formData.gender"
            is-link
            readonly
            label="性别"
            placeholder="选择性别"
            @click="showGenderPicker = true"
        />
        <van-field
            v-model="formData.initialPoints"
            type="number"
            label="初始积分"
            placeholder="请输入初始积分"
        />
        <van-field
            v-model="formData.roleTypeText"
            is-link
            readonly
            label="角色类型"
            @click="showRoleTypePicker = true"
        />
      </van-cell-group>

      <div style="margin: 16px;">
        <van-button
            round
            block
            type="primary"
            native-type="submit"
            class="van-button--warning"
        >
          提交
        </van-button>
      </div>
    </van-form>

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
          v-model="formData.roleTypeText"
          @confirm="onRoleTypeConfirm"
          @cancel="showRoleTypePicker = false"
      />
    </van-popup>
  </div>
</template>

<script src="./createUser.js"></script>


<style scoped>
.user-add-container {
  padding-bottom: 50px;
}

/* 移动端适配 */
@media (max-width: 768px) {
  :deep(.van-field__label) {
    width: 80px;
  }

  :deep(.van-field__control) {
    font-size: 14px;
  }
}

.van-button--warning {
  background-color: #4F75FF;
  border: none;
}

::v-deep input {
  background-color: aliceblue;
  height: 35px;
  text-align: right;
  padding-right: 10px;
}
</style>
