<template>
  <div class="ranking-page"  :style="{
    backgroundImage: `url(${require('../../assets/img/indexBg.png')})`,
    backgroundSize: 'cover',
    backgroundRepeat: 'no-repeat',
  }">
    <van-nav-bar title="选手积分排名" fixed />

    <van-tabs v-model:active="active" :style="{background: tabBackground,backgroundSize: 'contain',backgroundRepeat: 'no-repeat',marginTop: '50px',marginLeft: '10px',marginRight: '10px'}" @change="changeTab">
        <van-tab title="积分排行榜" style="color: white;width: 98%;">
          <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
            <van-list
              v-model:loading="loading"
              :finished="finished"
              finished-text="没有更多了"
              @load="onLoad"
            >
              <van-cell>
                <div class="player-item header">
                  <div class="avatar">
                    <div class="name">排名</div>
                  </div>
                  <div class="info">
                    <div class="name">姓名</div>
                  </div>
                  <div class="info">
                    <div class="points">累计积分</div>
                  </div>
                </div>
              </van-cell>
             <van-cell
                v-for="(player, index) in rankingList"
                :key="player.id"
                @click="getPlayerDetail(player.id)"
                style="height: 55px;"
             >
               <div class="player-item" :style="{
                    background: `url(${getBackgroundImage(index + 1)}) center center /contain no-repeat`
                  }">
                  <div class="avatar">
                    <van-image
                      round
                      :src="require('../../assets/img/first.png')"
                      width="50"
                      height="35"
                      v-if=" index === 0"
                    />
                    <van-image
                        round
                        :src="require('../../assets/img/second.png')"
                        width="50"
                        height="35"
                        v-if="index === 1"
                    />
                    <van-image
                        round
                        :src="require('../../assets/img/third.png')"
                        width="50"
                        height="35"
                        v-if=" index === 2"
                    />
                    <div class="rank" v-if="index > 2">{{ index+1}}</div>
                  </div>
                 <div class="info">
                    <div class="name">{{ player.playerName || player.name }}</div>
                 </div>
                 <div class="info">
                   <div class="points">{{ player.currentPoints }}</div>
                 </div>
               </div>
             </van-cell>
           </van-list>
          </van-pull-refresh>
        </van-tab>

      <van-tab title="对战记录">
          <van-pull-refresh v-model="matchesRefreshing" @refresh="onRefresh">
            <van-list
                v-model:loading="matchesLoading"
                :finished="matchesFinished"
                finished-text="没有更多了"
                @load="onLoad"
            >
              <van-swipe-cell
                  v-for="match in matchesList"
                  :key="match.matchId"

              >
                <van-cell
                    style="box-shadow: 0 1px 5px 1px rgb(44 63 192 / 20%);margin: 5px 20px;width: 90%;border-radius: 5px;padding: 20px 10px;"
                    clickable
                    @click="currentMatch = match; showMatchDetail = true"
                >
                  <!-- 使用 default 插槽自定义单元格内容 -->
                  <template #default>
                    <div class="match-info-container" style="color: #4a71ff;">
                      <!-- 比赛类型 -->
                      <span>{{ match.matchType }}</span>
                      <span> | </span>

                      <!-- 时间前的图片 -->
                      <van-image
                          round
                          :src="require('../../assets/img/time.png')"
                          width="12"
                          height="12"
                          class="time-image"
                      />

                      <!-- 比赛时间 -->
                      <span>{{ formatDateTime(match.matchTime) }}</span>
<!--                      <span> | </span>-->

<!--                      &lt;!&ndash; 比分 &ndash;&gt;-->
<!--                      <span>{{ match.redPoints }}:{{ match.bluePoints }}</span>-->
                    </div>
                    <div class="match-players">
                      <div style="display: flex;flex-direction: column;font-size: 15px; color: #4a71ff;justify-content: center;width: 5%;">

                      </div>
                      <div style="display: flex;flex-direction: column;font-size: 15px; color: black;justify-content: center;width: 25%;text-align: right;">
                        <span v-if="match.red_1 !==null">{{ formatTextWithSpace(match.red_1) }}</span>
                        <span v-if="match.red_2 !==null">  {{ formatTextWithSpace(match.red_2) }}</span>
                      </div>
                      <div style="display: flex;flex-direction: column;font-size: 15px;justify-content: center;width: 10%;">
                        <van-image
                            round
                            :src="require('../../assets/img/win.png')"
                            width="25"
                            height="25"
                            class="time-image"
                            v-if="match.winner === 'red'"
                        />
                      </div>
                      <div class="team red" style="display:flex;align-items: center;font-size: 20px;width: 5%;text-align: right;flex-direction: row;" >
                        {{ match.redPoints }}
                      </div>
                      <div class="vs" style="display: flex;justify-content: center;width: 10%;">
                         VS
                      </div>
                      <div class="team blue" style="display:flex;align-items: center;font-size: 20px;width: 5%;text-align: left;flex-direction: row-reverse;" >
                        {{ match.bluePoints }}
                      </div>

                        <div style="display: flex;flex-direction: column;font-size: 15px;justify-content: center;width: 10%;">
                          <van-image
                              round
                              :src="require('../../assets/img/win.png')"
                              width="25"
                              height="25"
                              class="time-image"
                              v-if="match.winner === 'blue'"
                          />
                        </div>
                        <div style="display: flex;flex-direction: column;font-size: 15px;color: black;justify-content: center;width: 25%;">
                          <span v-if="match.blue_1 !==null" >   {{ formatTextWithSpace(match.blue_1) }}</span>
                          <span v-if="match.blue_2 !==null">  {{ formatTextWithSpace(match.blue_2) }}</span>
                        </div>

                      <div style="display: flex;flex-direction: column;font-size: 15px; color: #4a71ff;justify-content: center;width: 5%;">

                      </div>
                    </div>
                  </template>
<!--                  <template #label>-->

<!--                  </template>-->
                </van-cell>

                <template #right>
                  <van-button
                      square
                      type="danger"
                      text="删除"
                      class="delete-button"
                      @click="handleDelete(match.matchId)"
                  />
                </template>
              </van-swipe-cell>
            </van-list>
          </van-pull-refresh>

          <div class="add-button">
            <van-button
                round
                type="primary"
                @click="handleAdd"
                v-if="addPlayers"
                style="border: none;background-color: white;color: #4a71ff;"
            >
              添加比赛
            </van-button>
          </div>
      </van-tab>

    </van-tabs>

    <van-popup
        v-model:show="showPlayerDetail"
        position="bottom"
        round
        :style="{ height: '70%' }"
    >
      <div class="player-detail" v-if="currentPlayer">
        <van-nav-bar
            :title="currentPlayer.user.playerName"
            left-text="返回"
            left-arrow
            @click-left="showPlayerDetail = false"
        />

        <div class="player-header">
          <van-image
              round
              width="80"
              height="80"

          />
          <div class="header-info">
            <h3>{{ currentPlayer.user.playerName }}</h3>
            <p>当前积分: {{ currentPlayer.user.currentPoints }}</p>
          </div>
        </div>

        <van-divider>比赛数据</van-divider>

        <van-cell-group>
          <van-cell title="单打比赛">
          <span v-if="currentPlayer.data">
                {{ currentPlayer.data.singleWin }} 胜
            {{ currentPlayer.data.singleMatches }} 负
                (胜率：{{ currentPlayer.singleWinRate.toFixed(1) }}%)
              </span>
            <span v-else>暂无数据</span>
          </van-cell>
          <van-cell title="双打比赛">
            <span v-if="currentPlayer.data">
                {{ currentPlayer.data.doubleWin }} 胜
              {{ currentPlayer.data.doubleMatches }} 负
                (胜率：{{ currentPlayer.doubleWinRate.toFixed(1) }}%)
              </span>
            <span v-else>暂无数据</span>
          </van-cell>
          <van-cell title="总得分">
              <span v-if="currentPlayer.data">
                {{ (currentPlayer.data.totalSscore || 0) + (currentPlayer.data.totalDscore || 0) }} 分
              </span>
              <span v-else>暂无数据</span>
          </van-cell>
        </van-cell-group>
      </div>
    </van-popup>
    <van-popup
        v-model:show="showAddMatchPopup"
        position="bottom"
        round
        closeable
        style="height: 85%"
    >
      <van-form >
        <van-cell-group inset>
          <van-cell title="新增比赛" class="form-title" />

          <!-- 比赛类型 -->
          <van-field
              v-model="matchForm.matchType"
              label="比赛类型"
              name="matchType"
              label-width="80px"
          >
            <!-- 使用input插槽插入单选按钮组 -->
            <template #input>
              <div class="custom-radio-group">
                <!-- 单打选项 -->
                <div
                    class="custom-radio"
                    :class="{ 'checked': matchForm.matchType === '单打' }"
                    @click="matchForm.matchType = '单打'"
                >
                  单打
                </div>

                <!-- 双打选项 -->
                <div
                    class="custom-radio"
                    :class="{ 'checked': matchForm.matchType === '双打' }"
                    @click="matchForm.matchType = '双打'"
                >
                  双打
                </div>
              </div>
            </template>
          </van-field>

          <!-- 比赛时间 -->
          <van-field
              v-model="matchForm.matchTime"
              label="比赛时间"
              name="matchTime"
              label-width="80px"
              placeholder="选择比赛时间"
              @click="showTimePicker = true"
              is-link
              readonly
          />

          <!-- 裁判选择 -->
          <van-field
              v-model="matchForm.refereeName"
              label="裁判"
              placeholder="点击选择裁判"
              readonly
              @click="showRefereePicker = true"
          />

          <!-- 红方选手1 -->
          <van-field
              v-model="matchForm.red_1"
              label="红方选手1"
              placeholder="点击选择选手"
              readonly
              @click="showRed1Picker = true"
              :rules="[{ required: true, message: '请选择红方选手1' }]"
          />

          <!-- 红方选手2（双打时显示） -->
          <van-field
              v-if="matchForm.matchType === '双打'"
              v-model="matchForm.red_2"
              label="红方选手2"
              placeholder="点击选择选手"
              readonly
              @click="showRed2Picker = true"
              :rules="[{ required: true, message: '请选择红方选手2' }]"
          />

          <!-- 蓝方选手1 -->
          <van-field
              v-model="matchForm.blue_1"
              label="蓝方选手1"
              placeholder="点击选择选手"
              readonly
              @click="showBlue1Picker = true"
              :rules="[{ required: true, message: '请选择蓝方选手1' }]"
          />

          <!-- 蓝方选手2（双打时显示） -->
          <van-field
              v-if="matchForm.matchType === '双打'"
              v-model="matchForm.blue_2"
              label="蓝方选手2"
              placeholder="点击选择选手"
              readonly
              @click="showBlue2Picker = true"
              :rules="[{ required: true, message: '请选择蓝方选手2' }]"
          />


          <!-- 红方得分 -->
          <van-field
              v-model.number="matchForm.redPoints"
              label="红方得分"
              name="redPoints"
              label-width="80px"
              type="number"
              placeholder="输入得分"
              :rules="formRules.redPoints"
          />

          <!-- 蓝方得分 -->
          <van-field
              v-model.number="matchForm.bluePoints"
              label="蓝方得分"
              name="bluePoints"
              label-width="80px"
              type="number"
              placeholder="输入得分"
              :rules="formRules.bluePoints"
          />
        </van-cell-group>

        <div style="margin: 16px;">
          <van-button round block type="primary" style="background-color: #4f75ff;color: white;border: none;width: 90%;margin-left: 5%;"  @click="submitMatchForm">
            提交
          </van-button>
        </div>
      </van-form>
    </van-popup>

    <!-- 裁判选择器 -->
    <van-popup v-model:show="showRefereePicker" position="bottom">
      <van-picker
          :columns="refereeOptions"
          @confirm="onRefereeConfirm"
          @cancel="showRefereePicker = false"
          show-toolbar
          title="选择裁判"
          value-key="name"
      />
    </van-popup>

    <van-popup v-model:show="showRed1Picker" position="bottom">
      <van-picker
          :columns="playerOptions"
          @confirm="onRed1Confirm"
          @cancel="showRed1Picker = false"
          show-toolbar
          title="选择选手"
          value-key="name"
      />
    </van-popup>
    <van-popup v-model:show="showRed2Picker" position="bottom">
      <van-picker
          :columns="playerOptions"
          @confirm="onRed2Confirm"
          @cancel="showRed2Picker = false"
          show-toolbar
          title="选择选手"
          value-key="name"
      />
    </van-popup>
    <van-popup v-model:show="showBlue1Picker" position="bottom">
      <van-picker
          :columns="playerOptions"
          @confirm="onBlue1Confirm"
          @cancel="showBlue1Picker = false"
          show-toolbar
          title="选择选手"
          value-key="name"
      />
    </van-popup>
    <van-popup v-model:show="showBlue2Picker" position="bottom">
      <van-picker
          :columns="playerOptions"
          @confirm="onBlue2Confirm"
          @cancel="showBlue2Picker = false"
          show-toolbar
          title="选择选手"
          value-key="name"
      />
    </van-popup>
<!--    比赛类型选择器-->
    <van-popup
        v-model="showMatchTypePicker"
        round
        position="bottom"
        destroy-on-close
    >
      <van-picker
          title="选择比赛类型"
          show-toolbar
          :columns="matchTypeOption"
          @confirm="onMatchTypeConfirm"
          @cancel="showMatchTypePicker = false"
      />
    </van-popup>

    <van-popup v-model:show="showTimePicker" position="bottom">
      <van-datetime-picker
          v-model="currentDate"
          type="datetime"
          title="选择比赛时间"
          :min-date="minDate"
          :max-date="maxDate"
          :formatter="formatter"
          @confirm="onTimeConfirm"
          @cancel="showTimePicker = false"
      />
    </van-popup>
  </div>
</template>

<script src="./rankingList.js"></script>


<style scoped>
.ranking-page {
  padding-top: 46px;
  padding-bottom: 50px;
}

.search-bar {
  padding: 10px;
  background: #f7f8fa;
}

.player-item {
  display: flex;
  align-items: center;
  padding: 10px 0;
}

.rank {
  //width: 30px;
  text-align: center;
  font-weight: bold;
  //color: #ee0a24;
  font-size: 16px;
}

.avatar {
  width: 20%;
  text-align: center;
  margin: 0 15px;
}

.info {
  flex: 1;
}

.name {
  font-size: 16px;
  margin-bottom: 5px;
  font-weight: bolder;
  text-align: center;
}

.points {
  font-size: 16px;
  margin-bottom: 5px;
  font-weight: bolder;
  text-align: center;
}

.player-detail {
  padding-bottom: 20px;
}

.player-header {
  display: flex;
  align-items: center;
  padding: 20px;
}

.header-info {
  margin-left: 15px;
}

.header-info h3 {
  margin: 0 0 5px 0;
  font-size: 18px;
}

.header-info p {
  margin: 0;
  color: #969799;
}

.match-players {
  display: flex;
  justify-content: center;
  margin-top: 8px;
  gap: 20px;
}

.team {
  flex: 1;
  text-align: center;
}

.team.red {
  color: #ee0a24;
}

.team.blue {
  color: #1989fa;
}

.vs {
  padding: 0 10px;
  font-weight: bolder;
  font-size: large;
  display: flex;
  align-items: center;
  color: #4a71ff;
}

.add-button {
  position: absolute;
  top: -65px;
  right: 38%;
  z-index: 99;
}

.player-detail, .match-detail {
  padding: 16px;
}

.delete-button {
  height: 100%;
}

.score-display {
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 20px 0;
}

.team-score {
  font-size: 24px;
  font-weight: bold;
  margin: 10px 0;
}

.match-title {
  text-align: center;
  margin-bottom: 5px;
}

.match-time {
  text-align: center;
  color: #969799;
  margin-bottom: 20px;
}

.match-result {
  text-align: center;
  margin: 20px 0;
}

::v-deep .van-tabs__nav {
  background-color: transparent !important;
}

::v-deep .van-tab {
  color: white;
  font-size: 19px;
  line-height: 70px;
  height: 50px;
  font-weight: bolder;
}

::v-deep .van-tab--active {
  color: #4b6ce4;
}

::v-deep .van-tabs--line .van-tabs__wrap {
  height: 70px;
}

::v-deep .van-tabs__line{
  background-color: transparent;
}

::v-deep .van-cell::after{
  border: none;
}

::v-deep .van-tabs__content{
  height: 590px;
  overflow-y: auto;
}

::v-deep input {
  background-color: aliceblue;
  height: 35px;
  text-align: right;
  padding-right: 10px;
}

/* 如果使用 scoped 样式，需添加穿透 */
::v-deep .van-radio {
  display: inline-flex !important;
}

::v-deep .van-radio__icon {
  display: block !important;  /* 确保单选按钮图标显示 */
}

.custom-radio-group {
  display: flex;
  gap: 16px;
}

.custom-radio {
  padding: 6px 16px;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
  width: 75px;
  text-align: center;
}

.custom-radio.checked {
  border-color: #4a71ff;
  background-color: #4a71ff;
  color: white;
  font-weight: 500;
}

.van-field__label{
  width: 5.7em;
}
::v-deep .van-cell{
  padding: 0 16px;
}
</style>
