<template>
  <div>

    <van-cell-group>
      <van-cell icon="setting-o" title="设置" is-link to="setting"/>
    </van-cell-group>

  </div>
</template>

<script src="./user.js"></script>

<style lang="less">
.user {
  &-poster {
    width: 100%;
    display: block;
  }

  &-group {
    margin-bottom: 15px;
  }

  &-links {
    padding: 15px 0;
    font-size: 12px;
    text-align: center;
    background-color: #fff;

    .van-icon {
      display: block;
      font-size: 24px;
    }
  }
}
</style>
