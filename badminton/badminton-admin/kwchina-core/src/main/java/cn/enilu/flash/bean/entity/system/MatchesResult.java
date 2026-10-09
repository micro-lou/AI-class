package cn.enilu.flash.bean.entity.system;


import cn.enilu.flash.bean.entity.BaseEntity;
import lombok.Data;
import org.hibernate.annotations.Table;

import javax.persistence.Column;
import javax.persistence.Entity;

@Entity(name = "t_matches_result")
@Table(appliesTo = "t_matches_result", comment = "结算结果表")
@Data
public class MatchesResult extends BaseEntity {


    @Column(name = "matches_sccore", columnDefinition = "结算得分")
    private int matchesScore;

    @Column(name = "user_id", columnDefinition = "比赛选手")
    private int userId;

    @Column(name = "matches_id", columnDefinition = "比赛场次")
    private int matchesId;

    @Column(name = "result_time", columnDefinition = "结算时间")
    private String resultTime;

}
