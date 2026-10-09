package cn.enilu.flash.dao.system;

import cn.enilu.flash.bean.entity.system.MatchesResult;
import cn.enilu.flash.bean.entity.system.ScoreChanges;
import cn.enilu.flash.dao.BaseRepository;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.util.List;


@Repository
public interface ScoreChangeRepository extends BaseRepository<ScoreChanges, Integer> {



}
