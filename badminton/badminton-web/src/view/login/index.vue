<template>
    <div>
            <van-cell-group>
<!--              <van-image height="100"
                         @click="toTopic(topic.id)"
                         src="@img/"></van-image>-->

              <img src="../../assets/img/login.png" height="714" width="1179" style="width:100% ;height: auto"/>
<!--              <van-field
                    v-model="mobile"
                    required
                    clearable
                    label="账号"
                    placeholder="请输入手机号"
            />
            </van-cell-group>
            <van-cell-group  v-show="show2">
            <van-field
                    v-model="password"
                    type="password"
                    label="密码"
                    placeholder="请输入密码"
                    required
            />-->
              <div  class="login_content">
                <span>用户名</span>
                <input placeholder="请输入手机号" class="inputContent"    v-model="mobile" >
                <span>密码</span>
                <input placeholder="请输入密码" class="inputContent" v-model="password"   type="password">
                <van-button type="warning" size="large"  v-show="show2" class="van-button--warning"  @click="loginByPass">登录</van-button>

              </div>

        </van-cell-group>
            <div class="button-group">
            <van-button type="warning" size="large"   v-show="show1" @click="loginOrRegister">立即登录/注册</van-button>

            <van-button type="info" size="large"   v-show="show1" @click="toLoginByPassword">用户名密码登录</van-button>

<!--            <van-button type="warning" size="large"  v-show="show2"  @click="loginByPass">登录</van-button>-->


            </div>

    </div>
</template>

<script src="./login.js"></script>

<style lang="less">
.login_content{
  display: flex;
  flex-direction: column;
  padding: 20px 40px;
  gap: 10px;
}
.inputContent{
  border: none;
  background: #F1F4FF;
  border-radius: 10px;
  height: 30px;
}

.van-button--warning {
  color: #fff;
  background-color: #4F75FF;
  border: none;
  border-radius: 10px;
}
    .button-group{
     margin: 15px;
        .van-button{
            margin-top: 10px;
        }
    }
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
