package cn.enilu.flash.dao.system;

import cn.enilu.flash.bean.entity.system.Users;
import cn.enilu.flash.dao.BaseRepository;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.data.repository.PagingAndSortingRepository;

import java.util.List;

public interface UsersRepository extends BaseRepository<Users,Long> {
    // 按id查询
    Users findById(Integer id);

    // 按选手姓名查询
    Users findByPlayerName(String playerName);

    // 按用户名查询
    Users findByUserName(String userName);

    // 按当前积分降序查询所有选手
    List<Users> findByRoleTypeOrderByCurrentPointsDesc(Integer roleType);

    // 按角色类型查询
    List<Users> findByRoleType(Integer roleType);

    // 按性别查询
    List<Users> findByGender(String gender);

    // 查询积分大于指定值的用户
    List<Users> findByCurrentPointsGreaterThan(Integer points);

    // 查询积分区间内的用户
    List<Users> findByCurrentPointsBetween(Integer minPoints, Integer maxPoints);

    // 通过方法名拼接 OR 条件
    List<Users> findByRoleTypeOrRoleType(Integer roleType1, Integer roleType2);

    Page<Users> findByRoleType(Integer roleType, Pageable pageable);

}
