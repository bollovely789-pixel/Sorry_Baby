#!/bin/bash

# Stop all V2Ray processes
pkill -f v2ray 2>/dev/null
sleep 2

echo "========================================="
echo "Testing V2Ray Configs"
echo "========================================="

for i in 1 2 3 4 5; do
    config="v2ray_${i}.json"
    
    if [ -f "$config" ]; then
        echo ""
        echo "📡 Testing $config..."
        
        # Get direct IP
        DIRECT_IP=$(curl -s --connect-timeout 5 https://api.ipify.org)
        echo "   Direct IP: $DIRECT_IP"
        
        # Start V2Ray
        v2ray run -config "$config" > /tmp/v2ray.log 2>&1 &
        V2RAY_PID=$!
        
        sleep 4
        
        # Test proxy
        PROXY_IP=$(curl --socks5 127.0.0.1:10808 -s --connect-timeout 5 https://api.ipify.org 2>/dev/null)
        
        if [ -n "$PROXY_IP" ]; then
            if [ "$PROXY_IP" != "$DIRECT_IP" ]; then
                echo "   ✅ WORKING! Proxy IP: $PROXY_IP"
            else
                echo "   ❌ IP not changed (still $PROXY_IP)"
            fi
        else
            echo "   ❌ Cannot connect through proxy"
            # Show error
            tail -3 /tmp/v2ray.log | head -3
        fi
        
        # Kill V2Ray
        kill $V2RAY_PID 2>/dev/null
        sleep 1
    fi
done

echo ""
echo "========================================="
pkill -f v2ray 2>/dev/null
