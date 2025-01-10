tact
// GameContract.tact
import "@stdlib/deploy";

// Storage Variables
const STORAGE_GAME_DATA: Int = 0x934;  // Game data storage ID
const MIN_TON_FOR_STORAGE: Int = 50000000; // 0.05 TON

// Game Constants 
const MAX_PET_LEVEL: Int = 100;
const MAX_COMBAT_LEVEL: Int = 100;
const PREMIUM_MULTIPLIER: Int = 150; // 1.5x as integer
const MIN_MINIBOSS_GOLD: Int = 50;

// Contract Data Structures
struct GameState {
    owner: Address;
    total_players: Int;
    players_map: map<Address, PlayerData>;
    last_update: Int;
}

struct PlayerData {
    user_id: Int;
    pet_level: Int;
    gold: Int; 
    gold_per_hour: Int;
    combat_level: Int;
    fire_coral: Int;
    is_premium: Bool;
    premium_expires: Int;
}

// Contract Messages
message AddPlayer {
    user_id: Int;
}

message UpdatePlayerStats {
    user_id: Int;
    pet_level: Int;
    gold: Int;
    gold_per_hour: Int; 
    combat_level: Int;
    fire_coral: Int;
}

message ActivatePremium {
    user_id: Int;
    duration: Int; // in seconds
}

contract GameContract {
    state: GameState;
    
    init() {
        self.state = GameState{
            owner: sender(),
            total_players: 0,
            players_map: emptyMap(),
            last_update: now()
        };
    }

    receive(msg: AddPlayer) {
        require(context().value >= MIN_TON_FOR_STORAGE, "Insufficient TON for storage");
        
        // Initialize player data
        let player = PlayerData{
            user_id: msg.user_id,
            pet_level: 1,
            gold: 0,
            gold_per_hour: 1,
            combat_level: 0,
            fire_coral: 0,
            is_premium: false,
            premium_expires: 0
        };
        
        // Add to players map
        self.state.players_map.set(sender(), player);
        self.state.total_players = self.state.total_players + 1;
    }

    receive(msg: UpdatePlayerStats) {
        let player = self.state.players_map.get(sender())!!;
        
        // Update stats
        player.pet_level = min(msg.pet_level, MAX_PET_LEVEL);
        player.gold = msg.gold;
        player.gold_per_hour = msg.gold_per_hour;
        player.combat_level = min(msg.combat_level, MAX_COMBAT_LEVEL);
        player.fire_coral = msg.fire_coral;
        
        // Apply premium multiplier if active
        if (player.is_premium && now() < player.premium_expires) {
            player.gold_per_hour = (player.gold_per_hour * PREMIUM_MULTIPLIER) / 100;
        }
        
        self.state.players_map.set(sender(), player);
    }

    receive(msg: ActivatePremium) {
        let player = self.state.players_map.get(sender())!!;
        player.is_premium = true;
        player.premium_expires = now() + msg.duration;
        self.state.players_map.set(sender(), player);
    }

    // Getter Methods
    get fun getPlayerStats(addr: Address): PlayerData {
        return self.state.players_map.get(addr)!!;
    }

    get fun getTotalPlayers(): Int {
        return self.state.total_players;
    }
}