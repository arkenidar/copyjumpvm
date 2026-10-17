int countdown(int n) {
    if (n == 0) {
        return 0;
    }
    output_int(n);
    return countdown(n - 1);
}

int main() {
    return countdown(3);
}
