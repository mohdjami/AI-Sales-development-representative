import Redis from "ioredis";

// Create a Redis instance.
// By default, it will connect to localhost:6379.
// We are going to cover how to specify connection options soon.
const redisUri = process.env.REDIS_URL!;

if (!redisUri) {
  throw new Error("Please provide a REDIS_URI in the environment variables");
}

const redis = new Redis(redisUri);

export default redis;
