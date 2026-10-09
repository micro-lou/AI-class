package cn.enilu.flash.service;

import cn.enilu.flash.bean.entity.system.Matches;
import cn.enilu.flash.bean.entity.system.ScoreChanges;
import cn.enilu.flash.bean.entity.system.ScoreRole;
import cn.enilu.flash.bean.entity.system.Users;
import cn.enilu.flash.service.system.MatchesService;
import cn.enilu.flash.service.system.ScoreChangesService;
import cn.enilu.flash.service.system.ScoreRuleService;
import cn.enilu.flash.service.system.UsersService;
import cn.enilu.flash.utils.EloUtils;
import cn.enilu.flash.utils.StringUtil;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;
import java.text.DecimalFormat;
import java.time.LocalDate;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

@Component
public class MatchTaskTimer {


    private final int BASE_SCORE = 32;

    private final String userPre = "user";

    @Autowired
    MatchesService matchesService;

    @Autowired
    ScoreRuleService scoreRuleService;

    @Autowired
    ScoreChangesService scoreChangesService;

    @Autowired
    UsersService usersService;

    DecimalFormat df = new DecimalFormat("0.00");


    @Transactional
//    @Scheduled(fixedRate = 300000) // 每5分钟一次
    @Scheduled(cron = "0 0 18 ? * SAT")
    public void performTask() {

        List<Users> allPlayers = this.usersService.findAllPlayers();

        // 所有选手当前的分数
        Map<String, Integer> userScores = new HashMap<>();
        for (Users allPlayer : allPlayers) {
            userScores.put(userPre + allPlayer.getId(), allPlayer.getCurrentPoints());
        }


        // 结算此次比赛的人员得分
        Map<String, Integer> userMatchScores = new HashMap<>();

        // 1、获取所有未结算的比赛
        List<Matches> matches = matchesService.findNoResultMatches();

        // 2、获取人员的的初始分
        List<ScoreRole> allRules = scoreRuleService.findAllRules();


        // 3、获取比赛的规则、计算得分
        for (Matches match : matches) {

            String red1 = match.getRed_1();
            String red2 = match.getRed_2();
            String blue1 = match.getBlue_1();
            String blue2 = match.getBlue_2();

            // 本周之前各选手的得分
            int red1LastScore = getUserScore(red1, userScores);
            int red2LastScore = getUserScore(red2, userScores);
            int blue1LastScore = getUserScore(blue1, userScores);
            int blue2LastScore = getUserScore(blue2, userScores);


            int redScore = 0;
            int blueScore = 0;
            // 判断单打 还是双打
            String matchType = match.getMatchType();
            if ("单打".equals(matchType)) {
                redScore = userScores.get(userPre + red1);
                blueScore = userScores.get(userPre + blue1);
            } else {
                redScore = (userScores.get(userPre + red1) + userScores.get(userPre + red2)) / 2;
                blueScore = (userScores.get(userPre + blue1) + userScores.get(userPre + blue2)) / 2;
            }

            double pSuccess = 0;
            //红队的比分大，此时红队的胜率比较大
            if (redScore > blueScore) {
                pSuccess = EloUtils.rating(redScore, blueScore);
                // 判断胜的队伍
                String winner = match.getWinner();
                // 红队胜
                if ("red".equals(winner)) {
                    // 胜者的得分
                    int redResult = (int) (BASE_SCORE * (1 - pSuccess));
                    calWinnerScore(redResult, red1, red2, match.getMatchId(), userMatchScores);
                    calLoserScore(redResult, blue1, blue1LastScore, blue2, blue2LastScore, match.getMatchId(), userMatchScores, allRules);
                } else {
                    // 胜者的得分
                    int blueResult = (int) (BASE_SCORE * pSuccess);
                    calWinnerScore(blueResult, blue1, blue2, match.getMatchId(), userMatchScores);
                    calLoserScore(blueResult, red1, red1LastScore, red2, red2LastScore, match.getMatchId(), userMatchScores, allRules);
                }
            } else {
                // 蓝队胜
                pSuccess = EloUtils.rating(blueScore, redScore);
                // 判断胜的队伍
                String winner = match.getWinner();
                // 红队胜
                if ("red".equals(winner)) {
                    int redResult = (int) (BASE_SCORE * pSuccess);
                    // 胜者的得分
                    calWinnerScore(redResult, red1, red2, match.getMatchId(), userMatchScores);
                    calLoserScore(redResult, blue1, blue1LastScore, blue2, blue2LastScore, match.getMatchId(), userMatchScores, allRules);
                } else {
                    // 胜者的得分
                    int blueResult = (int) (BASE_SCORE * (1 - pSuccess));
                    calWinnerScore(blueResult, blue1, blue2, match.getMatchId(), userMatchScores);
                    calLoserScore(blueResult, red1, red1LastScore, red2, red2LastScore, match.getMatchId(), userMatchScores, allRules);
                }
                // 把比赛设为已结算
                match.setIsValid(1);
                match.setSettlementTime(LocalDate.now().toString());
                this.matchesService.saveMatch(match);
            }
        }
        // 4、更新人员的最新分数
        Set<String> userKeys = userMatchScores.keySet();
        for (String userKey : userKeys) {
            if (StringUtil.isEmpty(userKey)) continue;
            String userId = userKey.replace(userPre, "");
            Users users = this.usersService.get(Long.parseLong(userId));
            if (users != null) {
                Integer currScore = userMatchScores.get(userKey);
                Integer currentPoints = users.getCurrentPoints();
                users.setCurrentPoints(currentPoints + currScore);
                this.usersService.save(users);
            }
        }

    }


    public int getUserScore(String userId, Map<String, Integer> userScores) {
        if (StringUtil.isEmpty(userId)) return 0;
        if (userScores.containsKey(userPre + userId)) {
            return userScores.get(userPre + userId);
        }
        return 1000;
    }


    // 计算胜者的得分
    private void calWinnerScore(int winScore, String winnerOne, String winnerTwo, int matchesId, Map<String, Integer> userMatchScores) {
        if (!StringUtil.isEmpty(winnerOne)) {
            String winnerOneUserId = userPre + winnerOne;
            if (userMatchScores.containsKey(winnerOneUserId)) {
                userMatchScores.put(winnerOneUserId, userMatchScores.get(winnerOneUserId) + winScore);
            } else {
                userMatchScores.put(winnerOneUserId, winScore);
            }
            ScoreChanges scoreChanges = new ScoreChanges();
            scoreChanges.setMatchId(matchesId);
            scoreChanges.setPlayerId(Integer.parseInt(winnerOne));
            scoreChanges.setPointsChange(winScore);
            scoreChanges.setIsSettled(1);
            // 记录积分结果
            scoreChangesService.insert(scoreChanges);
        }

        if (!StringUtil.isEmpty(winnerTwo)) {
            String winnerTwoUserId = userPre + winnerTwo;
            if (userMatchScores.containsKey(winnerTwoUserId)) {
                userMatchScores.put(winnerTwoUserId, userMatchScores.get(winnerTwoUserId) + winScore);
            } else {
                userMatchScores.put(winnerTwoUserId, winScore);
            }
            ScoreChanges scoreChanges = new ScoreChanges();
            scoreChanges.setMatchId(matchesId);
            scoreChanges.setPlayerId(Integer.parseInt(winnerTwo));
            scoreChanges.setPointsChange(winScore);
            scoreChanges.setIsSettled(1);
            // 记录积分结果
            scoreChangesService.insert(scoreChanges);
        }
    }

    // 计算败者的分数
    private void calLoserScore(int winScore, String loserOne, int loseOneScore, String loserTwo, int loseTwoScore, int matchesId, Map<String, Integer> userMatchScores, List<ScoreRole> allRules) {

        if (allRules == null || allRules.size() == 0) throw new RuntimeException("积分规则为空，请配置后再行运算");
        if (StringUtil.isEmpty(loserOne) && StringUtil.isEmpty(loserTwo))
            throw new RuntimeException("负者的人员Id为空，请校正后再试");

        for (ScoreRole allRule : allRules) {

            calRule(winScore, loserOne, loseOneScore, matchesId, userMatchScores, allRule);
            calRule(winScore, loserTwo, loseTwoScore, matchesId, userMatchScores, allRule);
        }
    }

    // 根据积分规则进行运算
    private void calRule(int winScore, String loserUser, int loseUserScore, int matchesId, Map<String, Integer> userMatchScores, ScoreRole itemRule) {

        if (StringUtil.isEmpty(loserUser)) return;

        Integer minScore = itemRule.getMinScore();
        Integer maxScore = itemRule.getCalRule();
        if (loseUserScore < minScore || loseUserScore > maxScore) return;

        float matchScore = 0;

        float score = itemRule.getScore();
        // 判断规则
        if (itemRule.getIsFix() == 1) {
            // 固定规则就是分值
            matchScore = score;
        } else {
            // 非固定规则就是以胜者的分为参考
            // 获取运算符
            String calSymbol = itemRule.getCalSymbol();
            if ("+".equals(calSymbol)) {
                matchScore = winScore + score;
            } else if ("-".equals(calSymbol)) {
                matchScore = winScore - score;
            } else if ("x".equals(calSymbol)) {
                matchScore = winScore * score;
            } else if ("÷".equals(calSymbol)) {
                matchScore = winScore / score;
            }
        }

        // 有小数点时，四舍五入
        int tmpScore = Math.round(matchScore);
        // 变更记录
        if (matchScore != 0) {
            ScoreChanges scoreChanges = new ScoreChanges();
            scoreChanges.setMatchId(matchesId);
            scoreChanges.setPlayerId(Integer.parseInt(loserUser));
            scoreChanges.setPointsChange(tmpScore);
            scoreChanges.setIsSettled(1);
            // 记录积分结果
            scoreChangesService.insert(scoreChanges);
            String loserUserId = userPre + loserUser;
            if (userMatchScores.containsKey(loserUserId)) {
                userMatchScores.put(loserUserId, userMatchScores.get(loserUserId) + tmpScore);
            } else {
                userMatchScores.put(loserUserId, tmpScore);
            }
        }
    }


}
