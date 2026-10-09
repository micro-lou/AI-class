package cn.enilu.flash.service.system;

import cn.enilu.flash.bean.dto.UserUpdateDTO;
import cn.enilu.flash.bean.entity.system.Users;
import cn.enilu.flash.dao.system.UsersRepository;
import cn.enilu.flash.service.BaseService;
import org.apache.shiro.util.StringUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import javax.persistence.criteria.Predicate;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

@Service
@Transactional
public class UsersService extends  BaseService<Users,Long, UsersRepository>  {

    @Autowired
    private UsersRepository usersRepository;

    // 创建或更新用户
    public Users save(Users user) {
        return usersRepository.save(user);
    }

    // 批量保存用户
    public List<Users> saveAll(Iterable<Users> users) {
        return usersRepository.saveAll(users);
    }

    // 按ID查询
    public Optional<Users> findById(Long id) {
        return usersRepository.findById(id);
    }



    // 查询所有裁判
    public List<Users> findAllReferees() {
        return usersRepository.findByRoleType(2);
    }

    public List<Users> findAllPlayers() {
        return usersRepository.findByRoleType(1);
    }

//


    // 更新用户积分
    public Users updateUserPoints(Long userId, Integer newPoints) {
        return usersRepository.findById(userId).map(user -> {
            user.setCurrentPoints(newPoints);
            return usersRepository.save(user);
        }).orElse(null);
    }

    // 删除用户
    public void delete(Long id) {
        usersRepository.deleteById(id);
    }

    // 检查用户名是否存在
    public boolean existsByUsername(String userName) {
        return usersRepository.findByUserName(userName) != null;
    }

    // 检查选手名是否存在
    public boolean existsByPlayerName(String playerName) {
        return usersRepository.findByPlayerName(playerName) != null;
    }

    public Page<Users> findByCondition(String keyword, Integer page, Integer pageSize) {
        Pageable pageable = PageRequest.of(page - 1, pageSize, Sort.by(Sort.Direction.DESC, "currentPoints"));

        Specification<Users> spec = (root, query, cb) -> {
            List<Predicate> predicates = new ArrayList<>();

            if (keyword != null && !keyword.trim().isEmpty()) {
                Predicate namePredicate = cb.like(root.get("playerName"), "%" + keyword + "%");
                Predicate usernamePredicate = cb.like(root.get("userName"), "%" + keyword + "%");
                predicates.add(cb.or(namePredicate, usernamePredicate));
            }

            return cb.and(predicates.toArray(new Predicate[0]));
        };

        return usersRepository.findAll(spec, pageable);
    }

    public Page<Users> findRankingByRoleType(Integer roleType, Integer page, Integer pageSize) {
        Pageable pageable = PageRequest.of(page - 1, pageSize, Sort.by(Sort.Direction.DESC, "currentPoints"));
        return usersRepository.findByRoleType(roleType, pageable);
    }

    @Transactional
    public void updateUser(UserUpdateDTO dto) {
        if (dto.getId() == null) {
            throw new IllegalArgumentException("用户ID不能为空");
        }
        // 2. 查询现有用户
        Users user = usersRepository.findById(dto.getId())
                .orElseThrow(() -> new IllegalArgumentException("用户不存在"));
        // 3. 复制可更新字段（忽略null值）
        if (dto.getUserName() != null) {
            user.setUserName(dto.getUserName());
        }
        if (dto.getPlayerName() != null) {
            user.setPlayerName(dto.getPlayerName());
        }
        if (dto.getGender() != null) {
            user.setGender(dto.getGender());
        }
        if (dto.getCurrentPoints() != null) {
            user.setCurrentPoints(dto.getCurrentPoints());
        }
        if (dto.getRoleType() != null) {
            user.setRoleType(dto.getRoleType());
        }

        // 4. 密码单独处理（加密且非空时更新）
        if (StringUtils.hasText(dto.getPassword())) {
            user.setPassword(encodePassword(dto.getPassword()));
        }

        // 5. 保存更新
        usersRepository.save(user);
    }

    /**
     * 模拟密码加密方法（根据实际项目替换）
     */
    private String encodePassword(String rawPassword) {
        // 实际项目中应使用 BCrypt 等加密方式
        return "加密后的密码:" + rawPassword.hashCode();
    }
}


